package main

import (
	"console/ui"

	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/theme"
)

func main() {
	a := app.New()
	a.Settings().SetTheme(theme.DarkTheme())
	w := a.NewWindow("Console")

	w.SetContent(ui.NewLayout(w))
	w.SetFullScreen(true)

	w.ShowAndRun()
}
