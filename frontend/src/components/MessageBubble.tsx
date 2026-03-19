import { useMemo, useState } from "react";
import ComparisonChart from "./ComparisonChart";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  isError?: boolean;
  sources?: { source?: string; url?: string; page?: number }[];
  comparison?: {
    comparison_mode: boolean;
    comparison_items: {
      strain: string;
      vendor: string;
      price?: string | null;
      mutation_gene?: string | null;
      key_use?: string | null;
    }[];
    comparison_fields: string[];
  };
};

type MessageBubbleProps = {
  message: Message;
};

type TableData = {
  headers: string[];
  rows: string[][];
};

function decodeHtmlEntities(value: string): string {
  if (!value) return value;
  const textarea = document.createElement("textarea");
  textarea.innerHTML = value;
  return textarea.value;
}

function normalizeCellText(value: string | null | undefined): string {
  return (value ?? "").replace(/\s+/g, " ").trim();
}

function extractTableData(table: HTMLTableElement): TableData | null {
  let headers: string[] = [];
  let rows: string[][] = [];

  const theadHeaders = Array.from(table.querySelectorAll("thead th, thead td")).map((cell) =>
    normalizeCellText(cell.textContent)
  );

  if (theadHeaders.length > 0) {
    headers = theadHeaders;
  }

  const tbodyRows = Array.from(table.querySelectorAll("tbody tr"));
  if (tbodyRows.length > 0) {
    rows = tbodyRows
      .map((row) =>
        Array.from(row.querySelectorAll("th, td")).map((cell) =>
          normalizeCellText(cell.textContent)
        )
      )
      .filter((row) => row.some((cell) => cell.length > 0));
  }

  // Fallback if table has no explicit thead/tbody
  if (headers.length === 0 && rows.length === 0) {
    const allRows = Array.from(table.querySelectorAll("tr"))
      .map((row) =>
        Array.from(row.querySelectorAll("th, td")).map((cell) =>
          normalizeCellText(cell.textContent)
        )
      )
      .filter((row) => row.some((cell) => cell.length > 0));

    if (allRows.length > 0) {
      headers = allRows[0];
      rows = allRows.slice(1);
    }
  }

  if (headers.length === 0 && rows.length === 0) {
    return null;
  }

  const columnCount = Math.max(
    headers.length,
    ...rows.map((row) => row.length),
    0
  );

  if (columnCount === 0) {
    return null;
  }

  const paddedHeaders =
    headers.length > 0
      ? [...headers, ...Array(Math.max(0, columnCount - headers.length)).fill("")]
      : Array.from({ length: columnCount }, (_, idx) => `Column ${idx + 1}`);

  const paddedRows = rows.map((row) => [
    ...row,
    ...Array(Math.max(0, columnCount - row.length)).fill(""),
  ]);

  return {
    headers: paddedHeaders,
    rows: paddedRows,
  };
}

function buildComparisonTable(
  comparison?: Message["comparison"]
): TableData | null {
  if (!comparison?.comparison_mode || !comparison.comparison_items?.length) {
    return null;
  }

  const headers = ["Strain", "Vendor", "Price", "Gene/Mutation", "Use"];
  const rows = comparison.comparison_items.map((item) => [
    normalizeCellText(item.strain),
    normalizeCellText(item.vendor),
    normalizeCellText(item.price),
    normalizeCellText(item.mutation_gene),
    normalizeCellText(item.key_use),
  ]);

  return { headers, rows };
}

function downloadTableAsCsv(tableData: TableData, filename = "table.csv") {
  const escapeCsv = (value: string) => `"${(value ?? "").replace(/"/g, '""')}"`;
  const lines = [
    tableData.headers.map(escapeCsv).join(","),
    ...tableData.rows.map((row) => row.map(escapeCsv).join(",")),
  ];

  const blob = new Blob([lines.join("\n")], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function DataTable({ tableData }: { tableData: TableData }) {
  return (
    <table className="w-full border-collapse text-xs text-slate-700">
      <thead>
        <tr>
          {tableData.headers.map((header, idx) => (
            <th
              key={`${header}-${idx}`}
              className="border border-slate-200 bg-slate-50 px-3 py-2 text-left font-semibold"
            >
              {header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {tableData.rows.map((row, rowIdx) => (
          <tr key={`row-${rowIdx}`}>
            {tableData.headers.map((_, cellIdx) => (
              <td
                key={`cell-${rowIdx}-${cellIdx}`}
                className="border border-slate-200 px-3 py-2 align-top"
              >
                {row[cellIdx] ?? ""}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const bubbleBase =
    "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed border";
  const bubbleStyle = isUser
    ? "bg-slate-900 text-white border-slate-900"
    : message.isError
      ? "bg-rose-50 text-rose-700 border-rose-200"
      : "bg-white text-slate-800 border-slate-200";

  const [showTable, setShowTable] = useState(false);
  const [showFullScreen, setShowFullScreen] = useState(false);

  const parsed = useMemo(() => {
    const rawContent = message.content ?? "";
    const decodedContent = decodeHtmlEntities(rawContent);

    const rawLooksLikeHtml = /<\/?[a-z][\s\S]*>/i.test(rawContent);
    const decodedLooksLikeHtml = /<\/?[a-z][\s\S]*>/i.test(decodedContent);

    const isHtml = !isUser && !message.isError && (rawLooksLikeHtml || decodedLooksLikeHtml);

    if (!isHtml) {
      return {
        isHtml: false,
        cleanedHtml: rawContent,
        table: null as TableData | null,
        text: rawContent,
      };
    }

    const parser = new DOMParser();
    const doc = parser.parseFromString(
      decodedLooksLikeHtml ? decodedContent : rawContent,
      "text/html"
    );

    const tableElement = doc.querySelector("table");
    const extractedTable = tableElement
      ? extractTableData(tableElement as HTMLTableElement)
      : null;

    if (tableElement) {
      tableElement.remove();
    }

    const cleanedHtml = doc.body.innerHTML || "";
    const text = normalizeCellText(doc.body.textContent || "");

    return {
      isHtml: true,
      cleanedHtml,
      table: extractedTable,
      text,
    };
  }, [isUser, message.isError, message.content]);

  const comparisonTable = useMemo(
    () => buildComparisonTable(message.comparison),
    [message.comparison]
  );

  const activeTableData = parsed.table ?? comparisonTable;

  const normalizedText = (parsed.text || message.content || "").toLowerCase();
  const headerText = activeTableData
    ? activeTableData.headers.join(" ").toLowerCase()
    : "";

  const hasVendorHeader = /vendor|company|supplier|brand|source/.test(headerText);
  const hasComparisonText =
    /compare|comparison|versus|vs\b|vendors|companies|suppliers|cheaper|price|pricing/.test(
      normalizedText
    );
  const hasMouseOrVendorContext =
    /mouse|mice|strain|vendor|company|supplier|jax|jackson|taconic|charles river|model/.test(
      normalizedText
    );

  const hasMultipleRows = !!activeTableData && activeTableData.rows.length > 1;
  const hasEnoughTableStructure =
    !!activeTableData &&
    activeTableData.headers.length > 0 &&
    activeTableData.rows.length > 0;

  const showTableButton =
    !!activeTableData &&
    hasEnoughTableStructure &&
    (
      !!message.comparison?.comparison_mode ||
      hasVendorHeader ||
      hasComparisonText ||
      hasMouseOrVendorContext ||
      hasMultipleRows
    );

  const isLargeTable =
    !!activeTableData &&
    (activeTableData.rows.length > 8 || activeTableData.headers.length > 5);

  const handleDownloadCsv = () => {
    if (!activeTableData) return;
    downloadTableAsCsv(activeTableData, "table.csv");
  };

  return (
    <>
      <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
        <div className={`${bubbleBase} ${bubbleStyle}`}>
          {message.comparison?.comparison_mode ? (
            <ComparisonChart payload={message.comparison} />
          ) : parsed.isHtml ? (
            parsed.cleanedHtml ? (
              <div
                className="chat-response"
                dangerouslySetInnerHTML={{ __html: parsed.cleanedHtml }}
              />
            ) : null
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}

          {showTableButton && (
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                onClick={() => setShowTable((prev) => !prev)}
              >
                {showTable ? "Hide Table" : "View as Table"}
              </button>

              {isLargeTable && (
                <button
                  type="button"
                  className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  onClick={() => setShowFullScreen(true)}
                >
                  Full Screen
                </button>
              )}
            </div>
          )}

          {showTable && activeTableData && (
            <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
              <DataTable tableData={activeTableData} />
            </div>
          )}

          {message.sources && message.sources.length > 0 && (
            <div className="mt-3 border-t border-slate-200/70 pt-2 text-xs text-slate-500">
              <p className="mb-1 font-medium text-slate-500">Sources</p>
              <ul className="space-y-1">
                {message.sources.map((source, idx) => {
                  const label = source.page ? `p.${source.page}` : "";
                  const text = `${source.source ?? "Unknown source"} ${label}`.trim();

                  return (
                    <li key={`${source.source ?? "source"}-${idx}`}>
                      {source.url ? (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-600 underline hover:text-slate-900"
                        >
                          {text}
                        </a>
                      ) : (
                        <span>{text}</span>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
      </div>

      {showFullScreen && activeTableData && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
          onClick={() => setShowFullScreen(false)}
        >
          <div
            className="w-full max-w-5xl rounded-2xl bg-white p-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-800">Table View</h3>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  onClick={handleDownloadCsv}
                >
                  Download Table
                </button>
                <button
                  type="button"
                  className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  onClick={() => setShowFullScreen(false)}
                >
                  Close
                </button>
              </div>
            </div>

            <div className="max-h-[70vh] overflow-auto rounded-xl border border-slate-200">
              <DataTable tableData={activeTableData} />
            </div>
          </div>
        </div>
      )}
    </>
  );
}