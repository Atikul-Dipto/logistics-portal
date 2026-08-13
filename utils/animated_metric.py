"""A JS-animated KPI row: cards fade/slide in on load and their
numbers count up from zero, rendered via a self-contained HTML
component (real browser JS, not a CSS-only illusion).
"""
import streamlit.components.v1 as components

_CARD_TEMPLATE = """
<div class="akpi-card" data-target="{value}" data-decimals="{decimals}" data-prefix="{prefix}" data-suffix="{suffix}">
  <div class="akpi-label">{label}</div>
  <div class="akpi-value">0</div>
</div>
"""

_PAGE_TEMPLATE = """
<div class="akpi-row">
  {cards}
</div>
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; background: transparent; }}
  .akpi-row {{
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
  }}
  .akpi-card {{
    flex: 1 1 150px;
    background: rgba(26, 29, 36, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 12px;
    padding: 16px 18px;
    opacity: 0;
    transform: translateY(14px);
    transition: transform 0.25s cubic-bezier(.22,1,.36,1), box-shadow .25s ease, border-color .25s ease;
  }}
  .akpi-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 18px 34px -20px rgba(91, 141, 239, 0.55);
    border-color: rgba(91, 141, 239, 0.55);
  }}
  .akpi-label {{
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #9aa3af;
    margin-bottom: 8px;
  }}
  .akpi-value {{
    font-family: 'Sora', 'Plus Jakarta Sans', sans-serif;
    font-size: 26px;
    font-weight: 700;
    color: #f4f6fb;
    letter-spacing: -0.01em;
  }}
  @keyframes akpiIn {{
    to {{ opacity: 1; transform: translateY(0); }}
  }}
  @media (max-width: 640px) {{
    .akpi-value {{ font-size: 22px; }}
    .akpi-card {{ padding: 14px; }}
  }}
</style>
<script>
  const cards = document.querySelectorAll('.akpi-card');
  cards.forEach((card, i) => {{
    const delay = i * 90;
    setTimeout(() => {{
      card.style.animation = 'akpiIn 0.5s cubic-bezier(.22,1,.36,1) forwards';
    }}, delay);

    const valueEl = card.querySelector('.akpi-value');
    const target = parseFloat(card.dataset.target);
    const decimals = parseInt(card.dataset.decimals, 10);
    const prefix = card.dataset.prefix || '';
    const suffix = card.dataset.suffix || '';
    const duration = 1100;
    const startTime = performance.now() + delay;

    function tick(now) {{
      const t = Math.min(1, Math.max(0, (now - startTime) / duration));
      const eased = 1 - Math.pow(1 - t, 3);
      const current = target * eased;
      valueEl.textContent = prefix + current.toLocaleString(undefined, {{
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }}) + suffix;
      if (t < 1) requestAnimationFrame(tick);
    }}
    requestAnimationFrame(tick);
  }});
</script>
"""


def animated_kpi_row(items, height=300):
    """height defaults generously (~3 rows) since this renders in a
    fixed-height iframe that can't auto-resize when flex-wrap kicks
    in on narrow viewports — the transparent background means any
    unused space on wider screens stays invisible."""
    """items: list of {label, value, prefix, suffix, decimals}"""
    cards_html = "".join(
        _CARD_TEMPLATE.format(
            value=item.get("value", 0),
            decimals=item.get("decimals", 0),
            prefix=item.get("prefix", ""),
            suffix=item.get("suffix", ""),
            label=item.get("label", ""),
        )
        for item in items
    )
    components.html(_PAGE_TEMPLATE.format(cards=cards_html), height=height, scrolling=False)
