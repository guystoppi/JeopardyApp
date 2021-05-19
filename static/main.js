function makeGame() {
    var roomname = $("#gamename").val();

    window.location = "/game/make/" + roomname + "/";
}


function goToQuestion(gamename, category, questionkey) {
    window.location = "/q/" + gamename + "/" + category + "/" + questionkey + "/";
}