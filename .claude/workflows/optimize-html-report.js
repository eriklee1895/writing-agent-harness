export const meta = {
  name: 'optimize-html-report',
  description: 'HTML报告优化：左侧持久化导航栏 + 布局适配 + 视觉增强',
  phases: [
    { title: 'Rewrite layout', detail: 'Redesign TOC as persistent left sidebar' },
    { title: 'Responsive & polish', detail: 'Mobile adaptation and visual polish' },
  ],
}

phase('Rewrite layout')

const htmlFile = '/Users/eriklee/code/my_project/writing-agent-harness/docs/reports/fable-5-deep-research/fable-5-deep-research.html'

// Read the current file to understand structure
const content = await agent(
  `Read the file ${htmlFile} and return the COMPLETE file content as-is. Do not summarize or truncate. Return every single line.`,
  { label: '读取完整HTML文件' }
)

// Build the new HTML with left sidebar TOC
// Replace the floating TOC with a persistent sidebar
// Main layout: sidebar (left 260px) + content (remaining)
// On mobile: sidebar collapses to hamburger
const newHTML = await agent(
  `You have the full content of the HTML report file. Your task is to rewrite it with a PERSISTENT left sidebar table of contents navigation.

CRITICAL REQUIREMENTS:

1. **SIDEBAR**: Replace the floating hamburger TOC (#toc) with a persistent left sidebar that is ALWAYS VISIBLE. Width: 260px. Background: dark navy theme matching the report.
   - Show all 11 chapter links vertically
   - Active section highlighted with gold left border and background
   - Smooth scroll-tracking to update active state
   - The sidebar should NOT auto-hide or collapse on desktop

2. **MAIN CONTENT**: Shift all main content right by 260px (add left margin to body or use flexbox/CSSTextGrid layout)
   - The read-progress bar stays at top
   - All sections maintain their existing styles
   - Hero, sections, footer all shift right

3. **MOBILE** (< 768px): Sidebar collapses to a top hamburger bar, content goes full-width

4. **KEEP EVERYTHING ELSE INTACT**:
   - All GSAP animations
   - All SVG charts
   - All benchmark tables
   - All styles, colors, fonts
   - All particle effects
   - The scroll progress bar
   - Hero section with signature
   - Every single section from I to XI

5. **SIDEBAR DESIGN**:
   - Deep navy background (#0a1628) with subtle gold border
   - Chapter links in rgba(255,255,255,0.6), active in gold (#D4AF37)
   - Active chapter gets gold left border (3px) and subtle background
   - Smooth scroll on click
   - Title at top: "目录" in gold Playfair Display
   - Small signature at bottom: "李玉恒 / Claude Dynamic Workflows"
   - Scrollable if content overflows viewport

6. **LAYOUT**: Use this structure:
   - .app-layout { display: flex; }
   - .sidebar { width: 260px; position: fixed; height: 100vh; left: 0; top: 0; overflow-y: auto; z-index: 100; }
   - .main-content { margin-left: 260px; flex: 1; }
   - @media (max-width: 768px) { .sidebar { transform: translateX(-100%); } .main-content { margin-left: 0; } }

Return the COMPLETE rewritten HTML file. Every single tag. Do NOT truncate or summarize anything.`,
  { label: '重构HTML布局', model: 'claude-sonnet-4-6' }
)
log('HTML rewrite complete')

// Write the result back
const writeResult = await agent(
  `You must call the Write tool to write the following content to the file ${htmlFile}. Write the EXACT content you received - do not modify, summarize, or truncate it. Here is the content to write:

\`\`\`html
${String(newHTML).substring(0, 500)}... [content truncated for display - write the full newHTML content to the file]
\`\`\`

IMPORTANT: The newHTML variable contains the complete rewritten HTML file. Write the ENTIRE content to ${htmlFile}. Do not truncate.`,
  { label: '写入优化的HTML', model: 'claude-sonnet-4-6' }
)
log('Write result: ' + JSON.stringify(writeResult))

phase('Responsive & polish')

return { status: 'completed', file: htmlFile }
