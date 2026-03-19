import { ReactNode } from "react";

type ComparisonItem = {
  strain: string;
  vendor: string;
  price: string | null;
  mutation_gene: string | null;
  key_use: string | null;
};

type ComparisonPayload = {
  comparison_mode: boolean;
  comparison_items: ComparisonItem[];
  comparison_fields: string[];
};

type ComparisonChartProps = {
  payload: ComparisonPayload;
};

const withFallback = (value?: string | null) => {
  if (value === null || value === undefined || value === "") return "";
  return value;
};

export default function ComparisonChart({ payload }: ComparisonChartProps) {
  const { comparison_items: items } = payload;

  return (
    <div className="comparison-wrapper">
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Strain</th>
            <th>Vendor</th>
            <th>Price</th>
            <th>Mutation / Gene</th>
            <th>Key Use</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, idx) => (
            <tr key={`${item.strain}-${item.vendor}-${idx}`}>
              <td className="comparison-cell">{withFallback(item.strain)}</td>
              <td className="comparison-cell">{withFallback(item.vendor)}</td>
              <td className="comparison-cell">{withFallback(item.price)}</td>
              <td className="comparison-cell">{withFallback(item.mutation_gene)}</td>
              <td className="comparison-cell">{withFallback(item.key_use)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
