package ui

import (
	"io"
	"os"
	"sync"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
)

// LogPanel captures Go log output and displays it in a scrollable panel.
type LogPanel struct {
	text   *widget.RichText
	scroll *container.Scroll
	mu     sync.Mutex
	lines  []string
}

// NewLogPanel creates a log panel, redirects the standard log package to it,
// and returns the panel plus its canvas object.
func NewLogPanel() (*LogPanel, fyne.CanvasObject) {
	lp := &LogPanel{}
	lp.text = widget.NewRichText(&widget.TextSegment{
		Text:  "",
		Style: widget.RichTextStyle{TextStyle: fyne.TextStyle{Monospace: true}},
	})
	lp.text.Wrapping = fyne.TextWrapOff
	lp.scroll = container.NewScroll(lp.text)

	return lp, lp.scroll
}

// Writer returns an io.Writer that appends to the log panel.
// Use it with log.SetOutput to capture application logs.
func (lp *LogPanel) Writer() io.Writer {
	return &logWriter{panel: lp, passthrough: os.Stderr}
}

type logWriter struct {
	panel       *LogPanel
	passthrough io.Writer
}

func (w *logWriter) Write(p []byte) (int, error) {
	// also write to stderr so logs aren't lost
	w.passthrough.Write(p)

	text := string(p)
	w.panel.mu.Lock()
	w.panel.lines = append(w.panel.lines, text)
	// keep last 500 lines
	if len(w.panel.lines) > 500 {
		w.panel.lines = w.panel.lines[len(w.panel.lines)-500:]
	}
	all := ""
	for _, l := range w.panel.lines {
		all += l
	}
	w.panel.mu.Unlock()

	fyne.Do(func() {
		w.panel.text.Segments = []widget.RichTextSegment{
			&widget.TextSegment{
				Text:  all,
				Style: widget.RichTextStyle{TextStyle: fyne.TextStyle{Monospace: true}},
			},
		}
		w.panel.text.Refresh()
		w.panel.scroll.ScrollToBottom()
	})

	return len(p), nil
}
