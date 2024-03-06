import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window

ApplicationWindow {
    id: mainwindow
    width: 800
    height: 400
    visible: true
    property QtObject guiHandler


    RowLayout {
        id: layout
        anchors.fill: parent

        Button {
            text: "Set text"
            objectName: "setTextButton"
            onClicked: guiHandler.handleButtonClick()
        }

        TextField {
            id: nameField
            objectName: "nameField"
            placeholderText: "Enter name"
            // onTextEdited: guiHandler.handleTextChanged()
        }

        Label {
            objectName: "dummyLabel"
            text: ""
        }
    }

    /*Connections {
        target: guiHandler

        function onSetText(text) {
            nameField.text = text;
        }
    }*/
}
