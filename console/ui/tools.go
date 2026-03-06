package ui

import (
	"os"
	"path/filepath"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
)

// TextViewer displays the contents of a selected file.
type TextViewer struct {
	header  *widget.Label
	content *widget.RichText
	scroll  *container.Scroll
}

// NewTextViewer creates a text viewer panel and returns the viewer and its canvas object.
func NewTextViewer() (*TextViewer, fyne.CanvasObject) {
	tv := &TextViewer{}
	tv.header = widget.NewLabelWithStyle("No file selected", fyne.TextAlignLeading, fyne.TextStyle{Bold: true})
	tv.content = widget.NewRichText(&widget.TextSegment{
		Text:  "",
		Style: widget.RichTextStyle{TextStyle: fyne.TextStyle{Monospace: true}},
	})
	tv.content.Wrapping = fyne.TextWrapOff
	tv.scroll = container.NewScroll(tv.content)

	return tv, container.NewBorder(tv.header, nil, nil, nil, tv.scroll)
}

// ShowFile reads the file at path and displays its contents.
// An empty path clears the viewer.
func (tv *TextViewer) ShowFile(path string) {
	if path == "" {
		tv.header.SetText("No file selected")
		tv.content.Segments = []widget.RichTextSegment{
			&widget.TextSegment{Text: "", Style: widget.RichTextStyle{TextStyle: fyne.TextStyle{Monospace: true}}},
		}
		tv.content.Refresh()
		return
	}
	data, err := os.ReadFile(path)
	if err != nil {
		tv.header.SetText("Error: " + err.Error())
		tv.content.Segments = []widget.RichTextSegment{
			&widget.TextSegment{Text: "", Style: widget.RichTextStyle{TextStyle: fyne.TextStyle{Monospace: true}}},
		}
		tv.content.Refresh()
		return
	}
	tv.header.SetText(filepath.Base(path))
	tv.content.Segments = []widget.RichTextSegment{
		&widget.TextSegment{
			Text:  string(data),
			Style: widget.RichTextStyle{TextStyle: fyne.TextStyle{Monospace: true}},
		},
	}
	tv.content.Refresh()
	tv.scroll.ScrollToTop()
}

// NewTools creates the right-pane: text viewer + machining calculators/references.
func NewTools(viewer fyne.CanvasObject, logsPanel fyne.CanvasObject) fyne.CanvasObject {
	tabs := container.NewAppTabs(
		container.NewTabItem("View", viewer),
		container.NewTabItem("Speeds & Feeds", toolPlaceholder("Speeds & Feeds calculator")),
		container.NewTabItem("Bolt Circle", toolPlaceholder("Bolt circle calculator")),
		container.NewTabItem("Tap Drill", toolPlaceholder("Tap drill chart")),
		container.NewTabItem("Trig", toolPlaceholder("Trig / geometry tools")),
		container.NewTabItem("Reference", toolPlaceholder("Reference tables")),
		container.NewTabItem("Logs", logsPanel),
	)
	tabs.SetTabLocation(container.TabLocationTop)

	return tabs
}

func toolPlaceholder(name string) fyne.CanvasObject {
	label := widget.NewLabelWithStyle(
		"not implemented",
		fyne.TextAlignCenter,
		fyne.TextStyle{Italic: true},
	)
	return container.NewCenter(label)
}
