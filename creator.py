#!/usr/bin/python3
import os
import shutil
import sys

from PyQt5 import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QPushButton, QHBoxLayout, QLineEdit, QComboBox, QFileDialog, \
    QMessageBox
from PyQt5.QtWidgets import QLabel, QWidget
from os.path import basename

# Covert internal naming with readable name
translation_gui = {
    "Name": "Name\t\t",
    "GenericName": "Generic name\t",
    "Type": "Type\t\t",
    "Exec": "Exec\t\t",
    "Icon": "Icon\t\t",
    "Terminal": "Terminal\t\t",
    "Path": "Auto generate Path",
    "Escape": "Auto escape Exec (spaces)",
}
# Contains all buttons
edit_list = {}
combo_list = {}
DESKTOP_PATH = os.path.expanduser("~/.local/share/applications/")
ICON_PATH = os.path.expanduser("~/.local/share/icons/hicolor")


def escape_string_shell(input_str):
    if combo_list["Escape"].currentText() == "No":
        return input_str
    escaped_input = input_str
    for invalid_char in [" "]:  # Only space for now
        escaped_input = escaped_input.replace(invalid_char, "\\" + invalid_char)
    return escaped_input


def create_selector_layout(name: str):
    _layout = QHBoxLayout()

    label = QLabel(translation_gui[name])
    line_edit = QLineEdit()

    # Remember edit for later
    edit_list[name] = line_edit

    _layout.addWidget(label)
    _layout.addWidget(line_edit)
    return _layout


def create_file_selector_layout(name: str):
    _layout = QHBoxLayout()

    label = QLabel(translation_gui[name])
    line_edit = QLineEdit()

    def click():
        file_path, _ = QFileDialog.getOpenFileName()
        line_edit.setText(file_path)

    search = QPushButton("Locate")
    search.clicked.connect(click)

    # Remember edit for later
    edit_list[name] = line_edit

    _layout.addWidget(label)
    _layout.addWidget(line_edit)
    _layout.addWidget(search)
    return _layout


def create_combo_layout(name: str, possibilities: list):
    _layout = QHBoxLayout()

    label = QLabel(translation_gui[name])
    line_combo = QComboBox()
    line_combo.addItems(possibilities)

    # Remember edit for later
    combo_list[name] = line_combo

    _layout.addWidget(label)
    _layout.addWidget(line_combo)
    return _layout


def create_debug_layout(_names: list, _destinations: list):
    _layout = QHBoxLayout()

    for name, destination in zip(_names, _destinations):
        def _run(_destination):
            def _secret():
                os.system("xdg-open " + _destination)
            return _secret

        button = QPushButton("Show " + name)
        button.clicked.connect(_run(destination))
        _layout.addWidget(button)
    return _layout


def copy_icon(icon_path: str, icon_name: str):
    # Copy icon where it needs to be
    image = QImage(icon_path)
    # Icon should be square
    height = image.height()
    acceptable_icon_size = [16, 24, 32, 48, 64, 128, 256, 512]
    closest_size = min(acceptable_icon_size, key=lambda x: abs(x - height))
    output_path = f"{ICON_PATH}/{closest_size}x{closest_size}/apps"
    shutil.copyfile(icon_path, f"{output_path}/{icon_name}.{icon_path.split('.')[-1]}")
    print(f"Icon: {icon_path} -> {output_path}")
    return icon_name


def generate_desktop(out_path: str):
    f = open(out_path, "w")
    f.write("[Desktop Entry]\n")

    # Writing all normal key / value
    desktop_name = edit_list["Name"].displayText()
    f.write(f"Name={desktop_name}\n")
    for i in ["GenericName"]:
        f.write(f"{i}={edit_list[i].displayText()}\n")

    # Special step for file/exec as I'm also adding executable Path
    gen_path = combo_list["Path"].currentText() == "Yes"
    exec_path = edit_list["Exec"].displayText()
    f.write(f"Exec={escape_string_shell(exec_path)}\n")
    if gen_path:
        f.write(f"Path={os.path.dirname(exec_path)}\n")

    # Special steps for icon (copy it first then on take file name)
    icon_path = edit_list["Icon"].displayText()
    if icon_path:
        icon = copy_icon(icon_path, desktop_name)
        f.write(f"Icon={icon}\n")

    # Adding more details
    for i in ["Type", "Terminal"]:
        f.write(f"{i}={combo_list[i].currentText()}\n")

    f.close()
    os.chmod(out_path, 0o775)


def post_run():
    # If there are refresh commands to run
    print("Refreshing icons")
    if shutil.which("gtk-update-icon-cache") is not None:
        os.system(f"gtk-update-icon-cache {ICON_PATH} -t")


def install_desktop():
    desktop_file = edit_list["Exec"].displayText()
    desktop_icon = edit_list["Icon"].displayText()
    # ToDo look inside desktop for icon
    copy_icon(desktop_icon, basename(desktop_file).replace(".desktop", ""))
    shutil.copyfile(desktop_file, f"{DESKTOP_PATH}/{basename(desktop_file)}")


def intercept(func):
    def show_error():
        try:
            func()
        except Exception as e:
            msg_box = QMessageBox()
            msg_box.setText(f"Error occurred: {e}")
            msg_box.exec()

    return show_error


@intercept
def run():
    print("-" * 10, "\nList")
    for i, j in edit_list.items():
        print("  ", i, j.displayText())
    print("Combo")
    for i, j in combo_list.items():
        print("  ", i, j.currentText())
    # CHECK first if input is .desktop is yes just install it with Icon
    desktop_path = DESKTOP_PATH + edit_list["Name"].displayText() + ".desktop"
    # desktop_path = "Test.desktop"
    is_desktop = edit_list["Exec"].displayText().endswith('.desktop')
    print("Desktop:", desktop_path)
    if not is_desktop:
        print("Generating Desktop shortcut")
        generate_desktop(desktop_path)
    else:
        print("Copying Desktop shortcut")
        install_desktop()
    post_run()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('Shortcut creator')
    window.setGeometry(200, 200, 500, 100)

    title = QLabel("<h1>Desktop Creator</h1>")
    title.setAlignment(Qt.Qt.AlignCenter)

    layout = QVBoxLayout()

    layout.addWidget(title)

    # Adding buttons trough layouts
    layout.addLayout(create_selector_layout("Name"))
    layout.addLayout(create_selector_layout("GenericName"))
    layout.addLayout(create_file_selector_layout("Exec"))
    layout.addLayout(create_file_selector_layout("Icon"))
    layout.addWidget(QLabel(""))
    layout.addLayout(create_combo_layout("Type", ["Application", "Link", "Directory"]))
    layout.addLayout(create_combo_layout("Terminal", ["false", "true"]))
    layout.addLayout(create_combo_layout("Path", ["No", "Yes"]))
    layout.addLayout(create_combo_layout("Escape", ["No", "Yes"]))

    # Final
    run_button = QPushButton('RUN')
    run_button.clicked.connect(run)
    layout.addWidget(run_button)
    window.setLayout(layout)

    # Debug
    names = ["shortcuts", "icons"]
    destinations = [DESKTOP_PATH, ICON_PATH]
    layout.addWidget(QLabel(""))
    layout.addLayout(create_debug_layout(names, destinations))

    window.show()
    sys.exit(app.exec_())
