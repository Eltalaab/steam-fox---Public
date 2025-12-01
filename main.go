package main

import (
	"bytes"
	_ "embed"
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	_ "image/jpeg"
	_ "image/png"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/driver/desktop"
	"fyne.io/fyne/v2/layout"
	"fyne.io/fyne/v2/theme"
	"fyne.io/fyne/v2/widget"
)

// --- دمج الأيقونة ---
//go:embed steam_fox_transparent.ico
var iconData []byte

// --- الألوان ---
var (
	ColBack      = color.RGBA{15, 15, 15, 255}
	ColCard      = color.RGBA{25, 25, 25, 255}
	ColTabBg     = color.RGBA{50, 50, 50, 255}   // خلفية شريط التبديل
	ColNeonGreen = color.RGBA{0, 230, 118, 255}
	ColRed       = color.RGBA{255, 76, 76, 255}
	ColOrange    = color.RGBA{255, 170, 0, 255}
	ColText      = color.RGBA{255, 255, 255, 255}
	ColGray      = color.RGBA{128, 128, 128, 255}
	ColDarkInput = color.RGBA{35, 35, 35, 255}
)

// --- المسارات ---
const (
	SteamPath = `C:\Program Files (x86)\Steam`
	TargetDir = SteamPath + `\config\stplug-in`
	SteamExe  = SteamPath + `\steam.exe`
)

// --- بيانات ---
var GamesDB = map[string][]struct{ Name, Link string }{
	"Ubisoft": {
		{"Assassin's Creed Mirage", "https://pixeldrain.com/api/file/mQr19FSK?download"},
		{"Far Cry 6", "https://drive.google.com/uc?export=download&confirm=t&id=1AnLR9TxK7-nbpYMP-fseXdmvOH2jO9jK"},
	},
	"Rockstar": {{"GTA V Enhanced", "https://pixeldrain.com/api/file/mV7oHSLZ?download"}},
	"EA Sports": {{"FC 23 (Fix)", "https://drive.google.com/uc?export=download&confirm=t&id=1cvp9tfw9pV2Nu21Hr5NghLclKOx4FK7i"}},
	"Activision": {{"Call of Duty MW2", "https://pixeldrain.com/api/file/Fq7dGXwd?download"}},
}

// --- الثيم ---
type exactTheme struct{}

func (m exactTheme) Color(name fyne.ThemeColorName, variant fyne.ThemeVariant) color.Color {
	switch name {
	case theme.ColorNameBackground: return ColBack
	case theme.ColorNameInputBackground: return ColDarkInput
	case theme.ColorNamePrimary: return ColNeonGreen
	case theme.ColorNameForeground: return ColText
	case theme.ColorNamePlaceHolder: return ColGray
	case theme.ColorNameScrollBar: return ColGray
	}
	return theme.DefaultTheme().Color(name, variant)
}
func (m exactTheme) Size(name fyne.ThemeSizeName) float32 {
	switch name {
	case theme.SizeNameInputRadius: return 8
	case theme.SizeNamePadding: return 10
	case theme.SizeNameText: return 13
	}
	return theme.DefaultTheme().Size(name)
}
func (m exactTheme) Icon(name fyne.ThemeIconName) fyne.Resource { return theme.DefaultTheme().Icon(name) }
func (m exactTheme) Font(style fyne.TextStyle) fyne.Resource    { return theme.DefaultTheme().Font(style) }


// --- عنصر "زر التبويب" المخصص (Clickable Tab Item) ---
type TabItemWidget struct {
	widget.BaseWidget
	Text     string
	IsActive bool
	OnTapped func()
}

func NewTabItemWidget(text string, active bool, tapped func()) *TabItemWidget {
	t := &TabItemWidget{Text: text, IsActive: active, OnTapped: tapped}
	t.ExtendBaseWidget(t)
	return t
}

func (t *TabItemWidget) CreateRenderer() fyne.WidgetRenderer {
	bg := canvas.NewRectangle(color.Transparent)
	bg.CornerRadius = 15 // Pill shape
	if t.IsActive {
		bg.FillColor = ColNeonGreen
	} else {
		bg.FillColor = color.Transparent
	}

	txt := canvas.NewText(t.Text, ColText)
	txt.TextStyle = fyne.TextStyle{Bold: true}
	txt.Alignment = fyne.TextAlignCenter
	if t.IsActive {
		txt.Color = color.Black // نص أسود على خلفية خضراء
	} else {
		txt.Color = ColText // نص أبيض على خلفية شفافة
	}

	return &tabItemRenderer{t, bg, txt, []fyne.CanvasObject{bg, txt}}
}

func (t *TabItemWidget) Tapped(_ *fyne.PointEvent) { if t.OnTapped != nil { t.OnTapped() } }

type tabItemRenderer struct {
	t   *TabItemWidget
	bg  *canvas.Rectangle
	txt *canvas.Text
	objs []fyne.CanvasObject
}
func (r *tabItemRenderer) Layout(s fyne.Size) {
	r.bg.Resize(s)
	r.txt.Resize(s)
	r.txt.Move(fyne.NewPos(0, (s.Height-r.txt.MinSize().Height)/2))
}
func (r *tabItemRenderer) MinSize() fyne.Size { return fyne.NewSize(140, 35) } // حجم الزر الواحد
func (r *tabItemRenderer) Refresh() {
	if r.t.IsActive {
		r.bg.FillColor = ColNeonGreen
		r.txt.Color = color.Black
	} else {
		r.bg.FillColor = color.Transparent
		r.txt.Color = ColText
	}
	canvas.Refresh(r.t)
}
func (r *tabItemRenderer) Objects() []fyne.CanvasObject { return r.objs }
func (r *tabItemRenderer) Destroy() {}


// --- زر مفرغ عادي (لباقي البرنامج) ---
type OutlinedButton struct {
	widget.BaseWidget
	Text        string
	IconRes     fyne.Resource
	Color       color.Color
	OnTapped    func()
	hovered     bool
}
func NewOutlinedButton(text string, icon fyne.Resource, col color.Color, tapped func()) *OutlinedButton {
	b := &OutlinedButton{Text: text, IconRes: icon, Color: col, OnTapped: tapped}
	b.ExtendBaseWidget(b)
	return b
}
func (b *OutlinedButton) CreateRenderer() fyne.WidgetRenderer {
	border := canvas.NewRectangle(color.Transparent)
	border.StrokeColor = b.Color
	border.StrokeWidth = 1.5
	border.CornerRadius = 8
	lbl := canvas.NewText(b.Text, b.Color)
	lbl.TextStyle = fyne.TextStyle{Bold: true}
	lbl.Alignment = fyne.TextAlignCenter
	var objects []fyne.CanvasObject
	var icon *canvas.Image
	if b.IconRes != nil {
		icon = canvas.NewImageFromResource(b.IconRes)
		icon.FillMode = canvas.ImageFillContain
		objects = []fyne.CanvasObject{border, lbl, icon}
	} else {
		objects = []fyne.CanvasObject{border, lbl}
	}
	return &outlinedButtonRenderer{b, border, lbl, icon, objects}
}
func (b *OutlinedButton) Tapped(_ *fyne.PointEvent) { if b.OnTapped != nil { b.OnTapped() } }
func (b *OutlinedButton) MouseIn(_ *desktop.MouseEvent) { b.hovered = true; b.Refresh() }
func (b *OutlinedButton) MouseOut() { b.hovered = false; b.Refresh() }
func (b *OutlinedButton) MouseMoved(_ *desktop.MouseEvent) {}

type outlinedButtonRenderer struct {
	b *OutlinedButton
	border *canvas.Rectangle
	lbl *canvas.Text
	icon *canvas.Image
	objects []fyne.CanvasObject
}
func (r *outlinedButtonRenderer) Layout(s fyne.Size) {
	r.border.Resize(s)
	iconSize := float32(20)
	textWidth := r.lbl.MinSize().Width
	var totalWidth float32
	if r.icon != nil { totalWidth = textWidth + iconSize + 10 } else { totalWidth = textWidth }
	startX := (s.Width - totalWidth) / 2
	if r.icon != nil {
		r.icon.Resize(fyne.NewSize(iconSize, iconSize))
		r.icon.Move(fyne.NewPos(startX, (s.Height-iconSize)/2))
		r.lbl.Resize(r.lbl.MinSize())
		r.lbl.Move(fyne.NewPos(startX + iconSize + 8, (s.Height-r.lbl.MinSize().Height)/2))
	} else {
		r.lbl.Resize(r.lbl.MinSize())
		r.lbl.Move(fyne.NewPos(startX, (s.Height-r.lbl.MinSize().Height)/2))
	}
}
func (r *outlinedButtonRenderer) MinSize() fyne.Size { return fyne.NewSize(150, 40) }
func (r *outlinedButtonRenderer) Refresh() {
	if r.b.hovered { r.border.FillColor = color.RGBA{50, 50, 50, 100} } else { r.border.FillColor = color.Transparent }
	r.border.StrokeColor = r.b.Color
	r.lbl.Color = r.b.Color
	canvas.Refresh(r.b)
}
func (r *outlinedButtonRenderer) Objects() []fyne.CanvasObject { return r.objects }
func (r *outlinedButtonRenderer) Destroy() {}

// --- API ---
type SteamItem struct { ID int `json:"id"`; Name string `json:"name"` }
type SteamSearchResponse struct { Items []SteamItem `json:"items"` }

func main() {
	myApp := app.New()
	myApp.Settings().SetTheme(&exactTheme{})
	
	appIcon := fyne.NewStaticResource("icon.ico", iconData)
	myApp.SetIcon(appIcon)

	w := myApp.NewWindow("Steam Fox")
	w.Resize(fyne.NewSize(950, 750))
	w.SetIcon(appIcon)

	// --- Header ---
	title := canvas.NewText("Steam Fox", ColText)
	title.TextStyle = fyne.TextStyle{Bold: true}
	title.TextSize = 28

	badgeBg := canvas.NewRectangle(ColNeonGreen)
	badgeBg.CornerRadius = 6
	badgeTxt := canvas.NewText(" v1.5 ", color.Black)
	badgeTxt.TextStyle = fyne.TextStyle{Bold: true}
	badgeTxt.TextSize = 12
	badge := container.NewStack(badgeBg, container.NewCenter(badgeTxt))

	webBtn := widget.NewButton("Open SteamDB", func() {
		u, _ := url.Parse("https://steamdb.info")
		myApp.OpenURL(u)
	})
	webBtn.Icon = theme.GridIcon()

	header := container.NewHBox(title, container.NewPadded(badge), layout.NewSpacer(), webBtn)

	// --- المحتوى (Content) ---
	// سنقوم بإنشاء المحتويين (الرئيسي والمكتبة) ونبدل بينهما
	
	// 1. محتوى Home
	homeContent := buildHomeContent()
	// 2. محتوى Library
	libContent, refreshLibFunc := buildLibraryContent()
	go refreshLibFunc()

	// الحاوية الرئيسية التي تتغير
	contentContainer := container.NewStack(homeContent)

	// --- تصميم شريط التبديل (Custom Tab Bar) ---
	
	var tabHome, tabLib *TabItemWidget

	switchTab := func(isHome bool) {
		if isHome {
			contentContainer.Objects = []fyne.CanvasObject{homeContent}
			tabHome.IsActive = true
			tabLib.IsActive = false
		} else {
			contentContainer.Objects = []fyne.CanvasObject{libContent}
			refreshLibFunc() // تحديث القائمة عند الفتح
			tabHome.IsActive = false
			tabLib.IsActive = true
		}
		tabHome.Refresh()
		tabLib.Refresh()
		contentContainer.Refresh()
	}

	tabHome = NewTabItemWidget("Home & Downloader", true, func() { switchTab(true) })
	tabLib = NewTabItemWidget("Library Manager", false, func() { switchTab(false) })

	// خلفية الشريط (Pill Background)
	barBg := canvas.NewRectangle(ColTabBg)
	barBg.CornerRadius = 20
	
	// تجميع الأزرار
	tabsRow := container.NewHBox(tabHome, tabLib)
	
	// تجميع الشريط بالكامل (خلفية + أزرار)
	// نستخدم container.NewStack لوضع الخلفية خلف الأزرار
	// لكن بما أن الأزرار شفافة، نحتاج لضبط الحجم.
	// الأفضل: وضع الخلفية داخل حاوية تحدد الحجم.
	
	// حاوية الشريط العائمة في المنتصف
	tabBar := container.NewStack(
		barBg,
		container.NewPadded(tabsRow), // Padded لعمل مسافة صغيرة حول الأزرار داخل الشريط
	)

	centeredTabBar := container.NewCenter(tabBar)


	// --- التجميع النهائي ---
	statusTxt := canvas.NewText("Ready.", ColGray)
	statusTxt.Alignment = fyne.TextAlignCenter
	footer := container.NewHBox(statusTxt)

	finalLayout := container.NewBorder(
		container.NewVBox(
			container.NewPadded(header),
			container.NewPadded(centeredTabBar), // الشريط في المنتصف أسفل الهيدر
		),
		container.NewPadded(footer),
		nil, nil,
		container.NewPadded(contentContainer),
	)

	w.SetContent(finalLayout)
	w.ShowAndRun()
}

// --- دوال بناء المحتوى (للتنظيم) ---

func buildHomeContent() fyne.CanvasObject {
	statusTxt := canvas.NewText("Ready.", ColGray)
	statusTxt.Alignment = fyne.TextAlignCenter
	statusTxt.TextSize = 12

	searchEntry := widget.NewEntry()
	searchEntry.SetPlaceHolder("App ID or Name")
	
	searchBtn := widget.NewButtonWithIcon("Search", theme.SearchIcon(), nil) 
	
	resultsBox := container.NewVBox()
	resultsScroll := container.NewVScroll(resultsBox)
	resultsScroll.SetMinSize(fyne.NewSize(0, 180))
	resultsScroll.Hide()

	searchBtn.OnTapped = func() {
		go func() {
			if searchEntry.Text == "" { return }
			statusTxt.Text = "Searching..."
			statusTxt.Color = ColGray
			statusTxt.Refresh()
			resultsBox.Objects = nil
			resultsScroll.Hide()
			url := fmt.Sprintf("https://store.steampowered.com/api/storesearch/?term=%s&l=english&cc=US", searchEntry.Text)
			resp, err := http.Get(url)
			if err == nil {
				defer resp.Body.Close()
				var res SteamSearchResponse
				json.NewDecoder(resp.Body).Decode(&res)
				for _, item := range res.Items {
					b := widget.NewButton(fmt.Sprintf("%s | ID: %d", item.Name, item.ID), func() {
						searchEntry.SetText(strconv.Itoa(item.ID))
						resultsScroll.Hide()
						statusTxt.Text = "Selected: " + item.Name
						statusTxt.Color = ColNeonGreen
						statusTxt.Refresh()
					})
					b.Alignment = widget.ButtonAlignLeading
					resultsBox.Add(b)
				}
				if len(res.Items) > 0 { resultsScroll.Show() }
			}
		}()
	}

	searchRow := container.NewBorder(nil, nil, searchBtn, nil, searchEntry)

	// Bypass Section
	bypassTitle := canvas.NewText("Direct Bypass Downloader", ColOrange)
	bypassTitle.TextStyle = fyne.TextStyle{Bold: true}
	bypassTitle.Alignment = fyne.TextAlignCenter
	bypassTitle.TextSize = 16

	catSelect := widget.NewSelect(getKeys(GamesDB), nil)
	catSelect.PlaceHolder = "Select Category"
	gameSelect := widget.NewSelect([]string{}, nil)
	gameSelect.PlaceHolder = "Select Category First"

	catSelect.OnChanged = func(s string) {
		var names []string
		for _, g := range GamesDB[s] { names = append(names, g.Name) }
		gameSelect.Options = names; gameSelect.Refresh()
	}

	dlBtn := widget.NewButtonWithIcon("Download", theme.DownloadIcon(), func() {
		cat := catSelect.Selected
		gm := gameSelect.Selected
		if cat != "" && gm != "" {
			for _, g := range GamesDB[cat] {
				if g.Name == gm {
					exec.Command("cmd", "/C", "start", g.Link).Start()
					return
				}
			}
		}
	})
	dlBtn.Importance = widget.HighImportance

	bypassContent := container.NewVBox(bypassTitle, layout.NewSpacer(), container.NewGridWithColumns(3, catSelect, gameSelect, dlBtn))
	bypassCard := createSmoothCard(bypassContent, ColDarkInput, 12)

	// Buttons
	btnAdd := NewOutlinedButton("Add Searched Game +", theme.ContentAddIcon(), ColNeonGreen, func() {
		id := searchEntry.Text
		if _, err := strconv.Atoi(id); err == nil {
			os.MkdirAll(TargetDir, 0755)
			ioutil.WriteFile(filepath.Join(TargetDir, id+".lua"), []byte(fmt.Sprintf("addappid(%s)", id)), 0644)
			statusTxt.Text = "Success! Game Added: " + id; statusTxt.Color = ColNeonGreen
		} else { statusTxt.Text = "Error"; statusTxt.Color = ColRed }
		statusTxt.Refresh()
	})

	btnRestart := NewOutlinedButton("Restart Steam ⚡", theme.ViewRefreshIcon(), ColRed, func() {
		exec.Command(SteamExe, "-shutdown").Start()
		go func() {
			time.Sleep(3 * time.Second)
			exec.Command("taskkill", "/F", "/IM", "steam.exe").Run()
			time.Sleep(1 * time.Second)
			exec.Command(SteamExe).Start()
		}()
	})

	homeBox := container.NewVBox(
		layout.NewSpacer(),
		createCenteredText("Enter Steam App ID or Search Game", ColGray),
		container.NewPadded(searchRow),
		container.NewPadded(resultsScroll),
		layout.NewSpacer(),
		bypassCard,
		layout.NewSpacer(),
		container.NewPadded(container.NewGridWithColumns(2, btnAdd, btnRestart)),
		layout.NewSpacer(),
	)

	return createSmoothCard(homeBox, ColCard, 20)
}

func buildLibraryContent() (fyne.CanvasObject, func()) {
	libBox := container.NewVBox()
	libScroll := container.NewVScroll(libBox)

	refreshLib := func() {
		libBox.Objects = nil
		files, _ := ioutil.ReadDir(TargetDir)
		for _, f := range files {
			if strings.HasSuffix(f.Name(), ".lua") {
				fName := f.Name()
				id := strings.TrimSuffix(fName, ".lua")
				txtTitle := widget.NewLabel("Game ID: " + id)
				txtTitle.TextStyle = fyne.TextStyle{Bold: true}
				delBtn := widget.NewButtonWithIcon("Delete", theme.DeleteIcon(), func() {
					os.Remove(filepath.Join(TargetDir, fName))
				})
				delBtn.Importance = widget.DangerImportance
				imgContainer := container.NewMax()
				go func(aid string, c *fyne.Container) {
					u := fmt.Sprintf("https://cdn.akamai.steamstatic.com/steam/apps/%s/header.jpg", aid)
					res, err := http.Get(u)
					if err == nil {
						d, _ := ioutil.ReadAll(res.Body); res.Body.Close()
						img, _, _ := image.Decode(bytes.NewReader(d))
						if img != nil {
							cImg := canvas.NewImageFromImage(img)
							cImg.FillMode = canvas.ImageFillContain
							cImg.SetMinSize(fyne.NewSize(120, 60))
							c.Objects = []fyne.CanvasObject{cImg}; c.Refresh()
						}
					}
				}(id, imgContainer)
				rowContent := container.NewBorder(nil, nil, imgContainer, delBtn, container.NewVBox(layout.NewSpacer(), txtTitle, layout.NewSpacer()))
				libBox.Add(createSmoothCard(rowContent, ColDarkInput, 10))
				libBox.Add(layout.NewSpacer())
			}
		}
		libBox.Refresh()
	}

	btnRefLib := widget.NewButtonWithIcon("Refresh List", theme.ViewRefreshIcon(), func(){ refreshLib() })
	layout := container.NewBorder(container.NewPadded(btnRefLib), nil, nil, nil, container.NewPadded(libScroll))
	return layout, refreshLib
}

// Helpers
func createSmoothCard(content fyne.CanvasObject, bgCol color.Color, radius float32) *fyne.Container {
	bg := canvas.NewRectangle(bgCol)
	bg.CornerRadius = radius
	return container.NewStack(bg, container.NewPadded(container.NewPadded(content)))
}
func createCenteredText(t string, c color.Color) *canvas.Text {
	txt := canvas.NewText(t, c)
	txt.Alignment = fyne.TextAlignCenter
	return txt
}
func getKeys(m map[string][]struct{ Name, Link string }) []string {
	keys := make([]string, 0, len(m))
	for k := range m { keys = append(keys, k) }
	return keys
}