package ui

import (
	"log"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/container"
)

// NewLayout builds the top-level split: file browser (left) | tools (right),
// wrapped in padding so content stays away from the window edges.
func NewLayout(w fyne.Window) fyne.CanvasObject {
	tv, viewerWidget := NewTextViewer()

	lp, logsWidget := NewLogPanel()
	log.SetOutput(lp.Writer())
	log.Println("console started")

	left := NewFileBrowser(w, tv.ShowFile)
	right := NewTools(viewerWidget, logsWidget)

	split := container.NewHSplit(left, right)
	split.Offset = 0.4

	return split
}
