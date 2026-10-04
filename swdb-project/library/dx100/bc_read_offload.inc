// BC forward-pass read offload, derived from Peter section 5 (E1-E5) plus BC-L1.
// Created: 2026-10-03 ET (ticket 42). Replaces the scalar PBFS of the
// scalar-only DX100 BC snapshot. DX100 performs the reads (frontier chunk,
// row bounds, range loop with continuation, neighbors, frontier vertex and the
// depth hint); the CPU keeps the compare-and-swap, the queue push, the
// successor bit and the path-count update. BC-L1: the path-count test reads
// the depth on the CPU after the compare-and-swap, never the DX100 hint.
// Memory regions: Brandes already registers queue, offsets, neighbors and
// depths (E3 reuse); this function registers nothing.
static dxc_context swdb_contexts[NUM_CORES];
static bool swdb_acceleration_enabled = false;
#ifndef SWDB_FRONTIER_THRESHOLD
#define SWDB_FRONTIER_THRESHOLD 64
#endif
#ifndef SWDB_CHUNK_SIZE
#define SWDB_CHUNK_SIZE TILE_SIZE
#endif
static_assert(SWDB_CHUNK_SIZE > 0 && SWDB_CHUNK_SIZE <= TILE_SIZE, "chunk capacity");
void PBFS(const Graph &g, SGOffset *VertexOffsetsData, NodeID source, pvector<CountT> &path_counts,
          Bitmap &succ, vector<SlidingQueue<NodeID>::iterator> &depth_index,
          SlidingQueue<NodeID> &queue, pvector<NodeID> &depths) {
 depths.fill(-1);
 depths[source] = 0;
 path_counts[source] = 1;
 queue.push_back(source);
 depth_index.push_back(queue.begin());
 queue.slide_window();
 const NodeID *g_out_start = g.out_neigh(0).begin();
 NodeID depth = 0;
 while (!queue.empty()) {
            std::cout << "Starting PBFS: " << queue.size() << " elements" << std::endl;
  depth++;
  const bool accelerate=swdb_acceleration_enabled&&queue.size()>=SWDB_FRONTIER_THRESHOLD;
#pragma omp parallel
  {
   QueueBuffer<NodeID> lqueue(queue);
   if(accelerate){
    dxc_context c=swdb_contexts[omp_get_thread_num()];
    __dxc_const_i32(1,c.reg[2]);__dxc_const_i32(0,c.reg[3]);
#pragma omp for schedule(dynamic,1)
    for(size_t begin=queue.shared_out_start;begin<queue.shared_out_end;begin+=SWDB_CHUNK_SIZE){
     const size_t end=std::min(begin+size_t(SWDB_CHUNK_SIZE),size_t(queue.shared_out_end));
     __dxc_const_i32(begin,c.reg[0]);__dxc_const_i32(end,c.reg[1]);
     __dxc_stream_load(queue.shared,c.reg[0],c.reg[1],c.reg[2],c.tile[0]);
     __dxc_gather(VertexOffsetsData,c.tile[0],c.tile[1]);
     __dxc_gather(VertexOffsetsData+1,c.tile[0],c.tile[2]);
     __dxc_const_i32(0,c.reg[4]);__dxc_const_i32(-1,c.reg[5]);
     __dxc_accelerated_chunk();
     for(;;){
      __dxc_range_loop(c.reg[4],c.reg[5],c.tile[1],c.tile[2],c.reg[2],c.tile[6],c.tile[7]);
      __dxc_wait(c.tile[7]);
      const unsigned count=__dxc_tile_size(c.tile[7]);if(count==0)break;
      __dxc_gather(g.out_neighbors_,c.tile[7],c.tile[0]);
      __dxc_gather(queue.shared+begin,c.tile[6],c.tile[3]);
      __dxc_gather(depths.data(),c.tile[0],c.tile[5]);
      __dxc_wait(c.tile[3]);__dxc_wait(c.tile[5]);
      int*vertices=__dxc_tile_pointer<int>(c.tile[0]);int*frontier=__dxc_tile_pointer<int>(c.tile[3]);
      int*hints=__dxc_tile_pointer<int>(c.tile[5]);int*edges=__dxc_tile_pointer<int>(c.tile[7]);
      for(unsigned k=0;k<count;++k){
       const NodeID v=vertices[k],u=frontier[k];const NodeID hint=hints[k];
       const bool claimed=hint==-1&&compare_and_swap(depths[v],static_cast<NodeID>(-1),depth);
       if(claimed){lqueue.push_back(v);}
       const NodeID fresh=__atomic_load_n(&depths[v],__ATOMIC_RELAXED);
       if(fresh==depth){
        succ.set_bit_atomic(edges[k]);
#pragma omp atomic
        path_counts[v] += path_counts[u];
       }
      }
     }
    }
   }else{
#pragma omp for schedule(dynamic, 64) nowait
    for (auto q_iter = queue.begin(); q_iter < queue.end(); q_iter++) {
     NodeID u = *q_iter;
     for (SGOffset vidx = VertexOffsetsData[u]; vidx < VertexOffsetsData[u + 1]; vidx++) {
      NodeID &v = g.out_neighbors_[vidx];
      if ((depths[v] == -1) && (compare_and_swap(depths[v], static_cast<NodeID>(-1), depth))) {
       lqueue.push_back(v);
      }
      if (depths[v] == depth) {
       succ.set_bit_atomic(&v - g_out_start);
#pragma omp atomic
       path_counts[v] += path_counts[u];
      }
     }
    }
   }
   lqueue.flush();
  }
  depth_index.push_back(queue.begin());
  queue.slide_window();
 }
 depth_index.push_back(queue.begin());
}
