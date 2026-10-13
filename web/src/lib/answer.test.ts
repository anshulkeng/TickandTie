import { describe, expect, it } from "vitest";

import { parse, splitGaps } from "./answer";

describe("parse", () => {
  it("turns citations into their own pieces", () => {
    expect(parse("Revenue was $416,161 million [F1].")).toEqual([
      { kind: "text", text: "Revenue was $416,161 million " },
      { kind: "cite", id: "F1" },
      { kind: "text", text: "." },
    ]);
  });

  it("reads risk-diff edits as removed and added text", () => {
    expect(parse("We [-may-] {+will+} grow.")).toEqual([
      { kind: "text", text: "We " },
      { kind: "removed", text: "may" },
      { kind: "text", text: " " },
      { kind: "added", text: "will" },
      { kind: "text", text: " grow." },
    ]);
  });

  it("keeps edits that span several lines", () => {
    expect(parse("[-first\nsecond-]")).toEqual([{ kind: "removed", text: "first\nsecond" }]);
  });

  it("leaves plain text alone", () => {
    expect(parse("No markup here.")).toEqual([{ kind: "text", text: "No markup here." }]);
  });
});

describe("splitGaps", () => {
  it("separates the Not covered part", () => {
    expect(splitGaps("Revenue was $1 million [F1]. Not covered: the rounding.")).toEqual({
      found: "Revenue was $1 million [F1].",
      gaps: "the rounding.",
    });
    expect(splitGaps("Revenue was $1 million [F1].")).toEqual({ found: "Revenue was $1 million [F1].", gaps: null });
  });
});