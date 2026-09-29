import csv
import io
import pandas as pd
from typing import List, Dict, Any

class ExportService:
    def to_csv(self, data: List[Dict[str, Any]]) -> str:
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    def to_xlsx(self, data: List[Dict[str, Any]]) -> bytes:
        if not data:
            return b""
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()
