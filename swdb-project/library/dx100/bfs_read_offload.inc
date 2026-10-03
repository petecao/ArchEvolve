// Peter section 5 read offload, fixes E1-E5. Updated: 2026-10-03 ET.
static dxc_context swdb_contexts[NUM_CORES];
static bool swdb_acceleration_enabled = false;
#ifndef SWDB_FRONTIER_THRESHOLD
#define SWDB_FRONTIER_THRESHOLD 64
#endif
#ifndef SWDB_CHUNK_SIZE
#define SWDB_CHUNK_SIZE TILE_SIZE
#endif
static_assert(SWDB_CHUNK_SIZE > 0 && SWDB_CHUNK_SIZE <= TILE_SIZE, "chunk capacity");
void TDStep(const Graph &g, pvector<SGOffset> &VertexOffsets, pvector<NodeID> &parent, SlidingQueue<NodeID> &queue, int num_nodes, int num_edges) {
#ifdef GEM5
 clear_mem_region();
 add_mem_region(queue.beginp(), queue.endp());
 add_mem_region(VertexOffsets.beginp(), VertexOffsets.endp());
 add_mem_region(g.out_neighbors_, &g.out_neighbors_[num_edges]);
 add_mem_region(parent.beginp(), parent.endp());
#endif
#pragma omp parallel
 {
  QueueBuffer<NodeID> lqueue(queue);
  const bool accelerate=swdb_acceleration_enabled&&queue.size()>=SWDB_FRONTIER_THRESHOLD;
  if(accelerate){
   dxc_context c=swdb_contexts[omp_get_thread_num()];
   __dxc_const_i32(1,c.reg[2]);__dxc_const_i32(0,c.reg[3]);
#pragma omp for schedule(dynamic,1)
   for(size_t begin=queue.shared_out_start;begin<queue.shared_out_end;begin+=SWDB_CHUNK_SIZE){
    const size_t end=std::min(begin+size_t(SWDB_CHUNK_SIZE),size_t(queue.shared_out_end));
    __dxc_const_i32(begin,c.reg[0]);__dxc_const_i32(end,c.reg[1]);
    __dxc_stream_load(queue.shared,c.reg[0],c.reg[1],c.reg[2],c.tile[0]);
    __dxc_gather(VertexOffsets.data(),c.tile[0],c.tile[1]);
    __dxc_gather(VertexOffsets.data()+1,c.tile[0],c.tile[2]);
    __dxc_const_i32(0,c.reg[4]);__dxc_const_i32(-1,c.reg[5]);
    __dxc_accelerated_chunk();
    for(;;){
     __dxc_range_loop(c.reg[4],c.reg[5],c.tile[1],c.tile[2],c.reg[2],c.tile[6],c.tile[7]);
     __dxc_wait(c.tile[7]);
     const unsigned count=__dxc_tile_size(c.tile[7]);if(count==0)break;
     __dxc_gather(g.out_neighbors_,c.tile[7],c.tile[0]);
     __dxc_gather(queue.shared+begin,c.tile[6],c.tile[3]);
     __dxc_gather(parent.data(),c.tile[0],c.tile[5]);
     __dxc_wait(c.tile[3]);__dxc_wait(c.tile[5]);
     int*vertices=__dxc_tile_pointer<int>(c.tile[0]);int*frontier=__dxc_tile_pointer<int>(c.tile[3]);
     int*hints=__dxc_tile_pointer<int>(c.tile[5]);
     for(unsigned k=0;k<count;++k){
      const NodeID v=vertices[k],u=frontier[k];const NodeID hint=hints[k];
      if(hint<0){
       const bool claimed=compare_and_swap(parent[v],hint,u);
       const int fresh=__atomic_load_n(&parent[v],__ATOMIC_RELAXED);
       __dxc_cas_probe(v,hint,claimed,g.out_degree(v)?-g.out_degree(v):-1,fresh,num_nodes);
       if(claimed){parent[v]=u;lqueue.push_back(v);}
      }
     }
    }
   }
  }else{
#pragma omp for nowait
   for(size_t i=queue.shared_out_start;i<queue.shared_out_end;++i){
    const NodeID u=queue.shared[i];
    for(int j=VertexOffsets[u];j<VertexOffsets[u+1];++j){
     const NodeID v=g.out_neighbors_[j],value=__atomic_load_n(&parent[v],__ATOMIC_RELAXED);
     if(value<0&&compare_and_swap(parent[v],value,u)){parent[v]=u;lqueue.push_back(v);}
    }
   }
  }
  lqueue.flush();
 }
#ifdef GEM5
 clear_mem_region();
#endif
}
