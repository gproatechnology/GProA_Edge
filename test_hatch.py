import ezdxf
doc = ezdxf.readfile(r'C:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\GProA_EOSIS_Edge\docs\Documentos_EOSIS\01_DESIGN_Areas_Loads\24044A250.dxf')
msp = doc.modelspace()
for hatch in msp.query('HATCH')[:1]:
    for path in hatch.paths:
        edges_list = list(path.edges)
        print(f'Edges count: {len(edges_list)}')
        for edge in edges_list[:5]:
            print(f'Edge type: {type(edge).__name__}')
            print(f'Has start: {hasattr(edge, "start")}')
            if hasattr(edge, 'start'):
                print(f'Start: {edge.start}')