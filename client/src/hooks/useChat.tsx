import { useState } from "react";
import { apiClient } from "@/lib/api";
import type { GenerateSqlResponse, ProviderType } from "@/lib/types";

type GenerateSQLProps = {
  prompt: string;
  db_id: number;
  provider_type?: ProviderType;
  model_name?: string;
};

type UseChatReturns = {
  response: string;
  loading: boolean;
  generateSQL: (props: GenerateSQLProps) => Promise<GenerateSqlResponse>;
};

export default function useChat(): UseChatReturns {
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const generateSQL = async ({
    prompt,
    db_id,
    provider_type = "gemini",
    model_name,
  }: GenerateSQLProps) => {
    setLoading(true);
    setResponse("");

    try {
      const res = await apiClient.generateSql({
        prompt,
        db_id,
        provider_type,
        model_name,
      });

      setResponse(res.data.raw_sql);
      return res.data;
    } catch (error) {
      console.error("Error generating SQL:", error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return {
    response,
    loading,
    generateSQL,
  };
}
