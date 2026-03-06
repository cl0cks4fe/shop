package ui

import (
	"fmt"
	"log"
	"path/filepath"
	"sync"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/theme"
	"fyne.io/fyne/v2/widget"
)

type fileBrowser struct {
	fs             *FileSystem
	files          []FileEntry
	mu             sync.Mutex
	folder         string
	parents        []string
	selName        string
	selPath        string
	list           *widget.List
	sendBtn        *widget.Button
	backBtn        *widget.Button
	header         *widget.Label
	onFileSelected func(path string)
}

func NewFileBrowser(w fyne.Window, onFileSelected func(path string)) fyne.CanvasObject {
	fs, err := NewFileSystem()
	if err != nil {
		log.Printf("filesystem: %v", err)
		return widget.NewLabel(fmt.Sprintf("Error: %v", err))
	}

	fb := &fileBrowser{fs: fs, onFileSelected: onFileSelected}
	fb.header = widget.NewLabelWithStyle(fs.RootName(), fyne.TextAlignLeading, fyne.TextStyle{Bold: true})
	fb.list = fb.makeList()
	fb.list.OnSelected = fb.onSelected

	fb.sendBtn = widget.NewButtonWithIcon("Send", theme.UploadIcon(), func() { fb.send() })
	fb.sendBtn.Importance = widget.HighImportance
	fb.sendBtn.Disable()

	fb.backBtn = widget.NewButton("←", func() { fb.back() })
	fb.backBtn.Disable()

	top := container.NewHBox(
		fb.backBtn,
		fb.header,
	)

	fb.load()
	log.Printf("file browser: loaded root %s", fs.RootName())

	return container.NewBorder(top, container.NewVBox(fb.sendBtn), nil, nil, fb.list)
}

func (fb *fileBrowser) makeList() *widget.List {
	return widget.NewList(
		func() int { fb.mu.Lock(); defer fb.mu.Unlock(); return len(fb.files) },
		func() fyne.CanvasObject {
			return container.NewHBox(widget.NewIcon(theme.FileIcon()), widget.NewLabel(""))
		},
		func(id widget.ListItemID, obj fyne.CanvasObject) {
			fb.mu.Lock()
			if id >= len(fb.files) { fb.mu.Unlock(); return }
			f := fb.files[id]
			fb.mu.Unlock()
			items := obj.(*fyne.Container).Objects
			if f.IsFolder {
				items[0].(*widget.Icon).SetResource(theme.FolderIcon())
			} else {
				items[0].(*widget.Icon).SetResource(theme.FileIcon())
			}
			items[1].(*widget.Label).SetText(f.Name)
		},
	)
}

func (fb *fileBrowser) load() {
	files, err := fb.fs.List(fb.folder)
	if err != nil {
		log.Printf("filesystem: %v", err)
		return
	}
	fb.mu.Lock()
	fb.files = files
	fb.mu.Unlock()
	if fb.folder == "" {
		fb.header.SetText(fb.fs.RootName())
	} else {
		path, err := filepath.Rel(fb.fs.Root(), fb.folder)
		if err != nil {
			return
		}
		fb.header.SetText(filepath.Join(fb.fs.RootName(), path))
	}
	fb.list.UnselectAll()
	fb.list.Refresh()
}

func (fb *fileBrowser) onSelected(id widget.ListItemID) {
	fb.mu.Lock()
	if id >= len(fb.files) { fb.mu.Unlock(); return }
	f := fb.files[id]
	fb.mu.Unlock()

	if f.IsFolder {
		log.Printf("file browser: opened folder %s", f.Name)
		fb.parents = append(fb.parents, fb.folder)
		fb.folder = f.Path
		fb.backBtn.Enable()
		fb.selName, fb.selPath = "", ""
		fb.sendBtn.Disable()
		if fb.onFileSelected != nil {
			fb.onFileSelected("")
		}
		fb.list.UnselectAll()
		fb.load()
		return
	}
	log.Printf("file browser: selected %s", f.Name)
	fb.selName, fb.selPath = f.Name, f.Path
	fb.sendBtn.Enable()
	if fb.onFileSelected != nil {
		fb.onFileSelected(f.Path)
	}
}

func (fb *fileBrowser) back() {
	n := len(fb.parents)
	if n == 0 { return }
	fb.folder = fb.parents[n-1]
	fb.parents = fb.parents[:n-1]
	if len(fb.parents) == 0 { fb.backBtn.Disable() }
	fb.selName, fb.selPath = "", ""
	fb.sendBtn.Disable()
	if fb.onFileSelected != nil {
		fb.onFileSelected("")
	}
	fb.load()
}

func (fb *fileBrowser) send() {
	if fb.selPath == "" {
		return
	}
	name, path := fb.selName, fb.selPath
	log.Printf("sending %s to gadget", name)

	fb.sendBtn.Disable()
	fb.sendBtn.SetText("Sending…")
	fb.sendBtn.Importance = widget.MediumImportance
	fb.sendBtn.Refresh()

	go func() {
		data, err := fb.fs.ReadFile(path)
		if err != nil {
			log.Printf("send: read error: %v", err)
			fyne.Do(func() { fb.setSendResult("Send Failed", widget.DangerImportance) })
			return
		}

		addr := GadgetAddress()
		if err := SendToGadget(addr, name, data); err != nil {
			log.Printf("send: upload error: %v", err)
			fyne.Do(func() { fb.setSendResult("Send Failed", widget.DangerImportance) })
			return
		}
		log.Printf("send: %s uploaded, waiting for transfer", name)

		ticker := time.NewTicker(2 * time.Second)
		defer ticker.Stop()
		for range ticker.C {
			if s := PingGadget(addr); !s.TransferActive {
				fyne.Do(func() { fb.setSendResult("Sent!", widget.SuccessImportance) })
				return
			}
		}
	}()
}

func (fb *fileBrowser) setSendResult(text string, importance widget.Importance) {
	fb.sendBtn.SetText(text)
	fb.sendBtn.Importance = importance
	fb.sendBtn.Enable()
	fb.sendBtn.Refresh()

	time.AfterFunc(5*time.Second, func() {
		fyne.Do(func() {
			fb.sendBtn.SetText("Send")
			fb.sendBtn.Importance = widget.HighImportance
			fb.sendBtn.Refresh()
		})
	})
}
