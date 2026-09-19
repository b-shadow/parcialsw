import { FormEvent, useState } from "react";
import { Plus } from "lucide-react";

import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Textarea } from "../../../shared/components/Textarea";

type ProjectFormProps = {
  onCreate: (payload: { name: string; description?: string }) => Promise<void>;
};

export function ProjectForm({ onCreate }: ProjectFormProps) {
  const [name, setName] = useState("Sistema de ventas");
  const [description, setDescription] = useState("Modelo colaborativo inicial");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (name.trim().length < 2) {
      return;
    }
    setLoading(true);
    try {
      await onCreate({ name: name.trim(), description: description.trim() || undefined });
      setName("");
      setDescription("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="grid gap-3" onSubmit={handleSubmit}>
      <Input label="Nombre del proyecto" value={name} onChange={(event) => setName(event.target.value)} />
      <Textarea
        label="Descripcion"
        value={description}
        onChange={(event) => setDescription(event.target.value)}
      />
      <Button disabled={loading} icon={<Plus size={18} aria-hidden="true" />} type="submit">
        {loading ? "Creando" : "Crear proyecto"}
      </Button>
    </form>
  );
}
