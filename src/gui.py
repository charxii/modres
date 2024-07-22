import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QScrollArea,
    QGroupBox,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from .resume import Resume


class ResumeCustomizerGUI(QMainWindow):
    def __init__(self, _as_debug: bool = False) -> None:
        super().__init__()

        # so i don't dox myself
        self.resume_path: str = (
            "personal_resume.txt"
            if os.path.exists("personal_resume.txt") and not _as_debug
            else "full_resume.txt"
        )

        self.resume = Resume(self.resume_path)
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("ModRes")
        self.setGeometry(100, 100, 1000, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Left side: Checkboxes
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(left_widget)

        for section in self.resume.sections:
            section_group = QGroupBox(section.title)
            section_layout = QVBoxLayout()
            section_checkbox = QCheckBox("Include Section")
            section_checkbox.setChecked(section.enabled)
            section_checkbox.stateChanged.connect(self.update_preview)
            section_layout.addWidget(section_checkbox)

            for item in section.content:
                if item["type"] == "entry":
                    item_text = f"{item.get('company', '')} - {item.get('title', '')}"
                    item_checkbox = QCheckBox(item_text)
                    item_checkbox.setChecked(item["enabled"])
                    item_checkbox.stateChanged.connect(self.update_preview)
                    section_layout.addWidget(item_checkbox)
                elif item["type"] == "list":
                    list_group = QGroupBox(item["group"])
                    list_layout = QVBoxLayout()

                    list_checkbox = QCheckBox("Include List")
                    list_checkbox.setChecked(item["enabled"])
                    list_checkbox.stateChanged.connect(self.update_preview)
                    list_layout.addWidget(list_checkbox)

                    for list_item in item["items"]:
                        item_checkbox = QCheckBox(list_item["text"])
                        item_checkbox.setChecked(list_item["enabled"])
                        item_checkbox.stateChanged.connect(self.update_preview)
                        list_layout.addWidget(item_checkbox)

                    list_group.setLayout(list_layout)
                    section_layout.addWidget(list_group)

            section_group.setLayout(section_layout)
            left_layout.addWidget(section_group)

        # Right side: Preview and buttons
        right_layout = QVBoxLayout()

        self.preview = QWebEngineView()
        right_layout.addWidget(self.preview)

        button_layout = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_resume)
        generate_button = QPushButton("Generate PDF")
        generate_button.clicked.connect(self.generate_pdf)
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(generate_button)

        right_layout.addLayout(button_layout)

        main_layout.addWidget(scroll_area, 1)
        main_layout.addLayout(right_layout, 2)

        self.update_preview()

    def update_preview(self) -> None:
        for section_group in self.findChildren(QGroupBox):
            section_title = section_group.title()
            section = next(
                (s for s in self.resume.sections if s.title == section_title), None
            )
            if section:
                checkboxes = section_group.findChildren(QCheckBox)
                section.enabled = checkboxes[0].isChecked()

                for item in section.content:
                    if item["type"] == "entry":
                        checkbox = next(
                            (
                                cb
                                for cb in checkboxes
                                if cb.text().startswith(
                                    f"{item.get('company', '')} - {item.get('title', '')}"
                                )
                            ),
                            None,
                        )
                        if checkbox:
                            item["enabled"] = checkbox.isChecked() and section.enabled
                    elif item["type"] == "list":
                        list_group = next(
                            (
                                g
                                for g in section_group.findChildren(QGroupBox)
                                if g.title() == item["group"]
                            ),
                            None,
                        )
                        if list_group:
                            item_checkboxes = list_group.findChildren(QCheckBox)
                            item["enabled"] = (
                                item_checkboxes[0].isChecked() and section.enabled
                            )
                            for i, list_item in enumerate(item["items"], start=1):
                                list_item["enabled"] = (
                                    item_checkboxes[i].isChecked() and item["enabled"]
                                )

        html_content = self.resume.to_html()
        with open("resume_style.css", "r") as css_file:
            css_content = css_file.read()

        full_html = f"""
        <html>
        <head>
            <style>{css_content}</style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        self.preview.setHtml(full_html)

    def refresh_resume(self) -> None:
        self.resume = Resume(self.resume_path)
        self._init_ui()

    def generate_pdf(self) -> None:
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Resume", "", "PDF Files (*.pdf)"
        )
        if file_name:
            self.preview.printToPdf(file_name)

    @staticmethod
    def run(_as_debug: bool = False) -> None:
        app = QApplication(sys.argv)
        ex = ResumeCustomizerGUI(_as_debug=_as_debug)
        ex.show()
        sys.exit(app.exec())
