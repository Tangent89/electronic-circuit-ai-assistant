export function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = String(text || "");
  return div.innerHTML;
}

export function sanitizeHtml(html) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(String(html || ""), "text/html");
  const blockedTags = ["script", "style", "iframe", "object", "embed", "link", "meta"];
  blockedTags.forEach((tag) => {
    doc.querySelectorAll(tag).forEach((node) => node.remove());
  });

  doc.querySelectorAll("*").forEach((element) => {
    [...element.attributes].forEach((attr) => {
      const name = attr.name.toLowerCase();
      const value = (attr.value || "").trim().toLowerCase();
      if (name.startsWith("on") || value.startsWith("javascript:")) {
        element.removeAttribute(attr.name);
        return;
      }
      if ((name === "href" || name === "src") && value) {
        const safe =
          value.startsWith("http://") ||
          value.startsWith("https://") ||
          value.startsWith("mailto:") ||
          value.startsWith("tel:") ||
          value.startsWith("#") ||
          value.startsWith("/") ||
          value.startsWith("./") ||
          value.startsWith("../");
        if (!safe) {
          element.removeAttribute(attr.name);
        }
      }
    });
  });

  return doc.body.innerHTML;
}

export function normalizeMathDelimiters(raw) {
  return String(raw || "")
    .replace(/\\\\\(/g, "\\(")
    .replace(/\\\\\)/g, "\\)")
    .replace(/\\\\\[/g, "\\[")
    .replace(/\\\\\]/g, "\\]");
}

export function protectMathSegments(raw) {
  const source = normalizeMathDelimiters(raw);
  const segments = [];
  const text = source.replace(
    /(\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|\$(?:\\.|[^$\n])+\$)/g,
    (match) => {
      const token = `@@MATH_${segments.length}@@`;
      segments.push(match);
      return token;
    }
  );
  return { text, segments };
}

export function restoreMathSegments(html, segments) {
  if (!segments || !segments.length) return html;
  return String(html || "").replace(/@@MATH_(\d+)@@/g, (_, idx) => {
    const math = segments[Number(idx)] || "";
    const isBlock = math.startsWith("$$") || math.startsWith("\\[");
    return isBlock
      ? `<div class="math-block">${math}</div>`
      : `<span class="math-inline">${math}</span>`;
  });
}

export function renderMarkdownWithMath(content) {
  const raw = String(content || "");
  const { text: protectedRaw, segments } = protectMathSegments(raw);
  let parsed = protectedRaw;

  if (window.marked) {
    try {
      parsed = window.marked.parse(protectedRaw, {
        gfm: true,
        breaks: true
      });
    } catch (e) {
      parsed = escapeHtml(protectedRaw).replace(/\n/g, "<br>");
    }
  } else {
    parsed = escapeHtml(protectedRaw).replace(/\n/g, "<br>");
  }

  const restored = restoreMathSegments(parsed, segments);
  return sanitizeHtml(restored);
}

export function renderPlainText(content) {
  return escapeHtml(content).replace(/\n/g, "<br>");
}

export function typesetMathInElement(element) {
  if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
    if (element) {
      return window.MathJax.typesetPromise([element]);
    }
    return window.MathJax.typesetPromise();
  }
  return Promise.resolve();
}
