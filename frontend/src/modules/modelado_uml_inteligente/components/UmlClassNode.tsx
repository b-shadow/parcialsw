import type { NodeProps } from "reactflow";
import { Handle, Position } from "reactflow";

type ClassNodeData = {
  name: string;
  stereotype?: string | null;
  attributes?: string[];
  methods?: string[];
};

export function UmlClassNode({ data }: NodeProps<ClassNodeData>) {
  return (
    <div className="w-56 overflow-hidden rounded-md border border-slate-400 bg-white text-xs shadow-sm">
      <Handle type="target" position={Position.Left} />
      <div className="border-b border-slate-300 bg-slate-100 px-3 py-2 text-center">
        {data.stereotype && <p className="text-[11px] text-slate-500">{`<<${data.stereotype}>>`}</p>}
        <p className="font-semibold text-ink">{data.name}</p>
      </div>
      <div className="min-h-12 border-b border-slate-300 px-3 py-2 text-slate-700">
        {(data.attributes?.length ? data.attributes : ["- id: UUID"]).map((attribute) => (
          <p key={attribute}>{attribute}</p>
        ))}
      </div>
      <div className="min-h-12 px-3 py-2 text-slate-700">
        {(data.methods?.length ? data.methods : ["+ validar(): boolean"]).map((method) => (
          <p key={method}>{method}</p>
        ))}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
