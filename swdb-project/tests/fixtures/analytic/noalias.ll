; Independent metadata-only call fixture. Updated: 2026-10-06 ET.
source_filename = "noalias.ll"
declare void @llvm.experimental.noalias.scope.decl(metadata)
define i32 @metadata_hint() #0 !dbg !4 {
entry:
  call void @llvm.experimental.noalias.scope.decl(metadata !0), !dbg !8
  ret i32 0, !dbg !8
}
define i32 @main() {
  %result = call i32 @metadata_hint()
  ret i32 %result
}
attributes #0 = { noinline }
!0 = !{!1}
!1 = distinct !{!1, !2, !"Independent scope"}
!2 = distinct !{!2, !"Independent domain"}
!llvm.dbg.cu = !{!7}
!llvm.module.flags = !{!9, !10}
!4 = distinct !DISubprogram(name: "metadata_hint", scope: !5, file: !5, line: 1, type: !6, scopeLine: 1, spFlags: DISPFlagDefinition, unit: !7)
!5 = !DIFile(filename: "noalias.ll", directory: ".")
!6 = !DISubroutineType(types: !11)
!7 = distinct !DICompileUnit(language: DW_LANG_C_plus_plus, file: !5, producer: "Independent fixture", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug)
!8 = !DILocation(line: 1, column: 1, scope: !4)
!9 = !{i32 7, !"Dwarf Version", i32 5}
!10 = !{i32 2, !"Debug Info Version", i32 3}
!11 = !{!12}
!12 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
