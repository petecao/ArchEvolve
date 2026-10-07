// New bounded host fixture for HTA Fig. 8 slow-lookup recheck.
// Mutex-protected cache slot stands for an atomic HTA result.
// This is not ISA execution.
#include <cassert>
#include <condition_variable>
#include <cstdint>
#include <iostream>
#include <mutex>
#include <optional>
#include <thread>
#include <unordered_map>

using Word = std::uint64_t;

struct State
{
    std::mutex hardwareMutex;
    std::mutex softwareMutex;
    Word hardwareKey = 17;
    Word hardwareValue = 7;
    std::unordered_map<Word, Word> software{{39, 11}};

    std::optional<Word> atomicLookup(Word key)
    {
        std::lock_guard<std::mutex> lock(hardwareMutex);
        if (key == hardwareKey)
            return hardwareValue;
        return std::nullopt; // Nonmatching fully occupied fixture slot.
    }

    void lockedSwap(Word key, Word value)
    {
        std::lock_guard<std::mutex> fallback(softwareMutex);
        std::lock_guard<std::mutex> hardware(hardwareMutex);
        software[hardwareKey] = hardwareValue;
        hardwareKey = key;
        hardwareValue = value;
        software.erase(key);
    }
};

std::optional<Word> racedLookup(bool recheck, Word newValue)
{
    State state;
    std::mutex eventMutex;
    std::condition_variable event;
    bool firstMiss = false;
    bool migrationComplete = false;
    std::optional<Word> result;

    std::thread lookupActor([&] {
        assert(!state.atomicLookup(39));
        {
            std::unique_lock<std::mutex> lock(eventMutex);
            firstMiss = true;
            event.notify_all();
            event.wait(lock, [&] { return migrationComplete; });
        }
        std::lock_guard<std::mutex> fallback(state.softwareMutex);
        if (recheck) {
            auto current = state.atomicLookup(39);
            if (current.has_value()) {
                result = current;
                return;
            }
        }
        auto it = state.software.find(39);
        if (it != state.software.end())
            result = it->second;
    });
    std::thread insertionActor([&] {
        {
            std::unique_lock<std::mutex> lock(eventMutex);
            event.wait(lock, [&] { return firstMiss; });
        }
        state.lockedSwap(39, newValue);
        {
            std::lock_guard<std::mutex> lock(eventMutex);
            migrationComplete = true;
        }
        event.notify_all();
    });
    lookupActor.join();
    insertionActor.join();
    assert(state.atomicLookup(39).value() == newValue);
    assert(state.software.at(17) == 7);
    assert(state.software.count(39) == 0);
    return result;
}

std::optional<Word> noMigrationLookup(State &state, Word key)
{
    if (auto fast = state.atomicLookup(key); fast.has_value())
        return fast;
    std::lock_guard<std::mutex> fallback(state.softwareMutex);
    if (auto rechecked = state.atomicLookup(key); rechecked.has_value())
        return rechecked;
    auto it = state.software.find(key);
    return it == state.software.end() ? std::nullopt :
                                       std::optional<Word>(it->second);
}

int main()
{
    // Key39 exists continuously: software11 -> atomic hardware99. A missing
    // result cannot be linearized to any instant in this interleaving.
    assert(!racedLookup(false, 99).has_value());
    assert(racedLookup(true, 99).value() == 99);
    assert(racedLookup(true, 0).has_value()); // Returned zero is still a hit.
    State state;
    assert(noMigrationLookup(state, 39).value() == 11);
    assert(noMigrationLookup(state, 17).value() == 7);
    assert(!noMigrationLookup(state, 100).has_value());
    std::cout << "missing post-lock recheck reproduced; repaired migration, "
                 "zero-value, fallback, fast-hit and missing-key cases PASS\n";
}
