/*
 *     Copyright (c) 2021 Przemysław Buczkowski
 *
 *     This file is part of Anime Quiz.
 *
 *     Anime Quiz is free software: you can redistribute it and/or modify
 *     it under the terms of the GNU Affero General Public License as
 *     published by the Free Software Foundation, either version 3 of
 *     the License, or (at your option) any later version.
 *
 *     Anime Quiz is distributed in the hope that it will be useful,
 *     but WITHOUT ANY WARRANTY; without even the implied warranty of
 *     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *     GNU Affero General Public License for more details.
 *
 *     You should have received a copy of the GNU Affero General Public License
 *     along with Anime Quiz.  If not, see <https://www.gnu.org/licenses/>.
 */

Object.defineProperty(HTMLMediaElement.prototype, 'playing', {
    get: function(){
        return !!(this.currentTime > 0 && !this.paused && !this.ended && this.readyState > 2);
    }
})

function addUser() {
    const template = document.getElementById("username-template");

    document.getElementById("addUserBtn").insertAdjacentHTML(
        "beforebegin", template.innerHTML
    );
}

function removeUser(element) {
    element.parentNode.parentNode.removeChild(element.parentNode);
}

document.addEventListener("DOMContentLoaded", function() {
    const count = document.getElementById('count');
    const details = document.getElementById('details');
    const player = document.getElementById('player');

    let time = parseInt(sessionStorage.getItem("time"));
    if (isNaN(time)) time = 10;

    let waiting = false; // True when waiting for data.

    function play() {
        player.removeEventListener('canplaythrough', play);

        function step() {
            if (time > 1) {
                if (player.playing)
                    time--;
                count.innerText = time.toString();
                setTimeout(step, 1000);
            }
            else {
                player.style.visibility = 'visible';
                details.style.visibility = 'visible';
                count.innerHTML = "";
            }
        }

        player.play().then(() => {
            count.innerText = time.toString();
            if (time === 0)
                step();
            else
                setTimeout(step, 1000);
        }).catch(() => {
            count.innerText = "Enable Autoplay (in the address bar) and press Play!";
       });
    }


    player.addEventListener('canplaythrough', play);
    player.addEventListener('ended', () => {
        document.getElementById('settings').submit();
    });
    player.addEventListener('waiting', () => { waiting = true; })
    player.addEventListener('playing', () => { waiting = false; })

    initColorMode();
});

function addPlayer() {
    const li = document.querySelector(
        "template#results-template"
    ).content.children[0].firstElementChild.cloneNode(true);
    document.getElementById("results").appendChild(li);
}

function removePlayer(element){
    element.parentNode.parentNode.parentNode.removeChild(element.parentNode.parentNode)
}

function clearPlayer(){
    sessionStorage.removeItem('results');
    document.getElementById("results-div").innerHTML = document.getElementById('results-template').innerHTML;
}

function addPoint(element){
    let current = element.parentNode.getElementsByClassName("points")[0].innerText;
    current = parseInt(current) + 1;
    element.parentNode.getElementsByClassName("points")[0].innerText = current;
}

function removePoint(element){
    let current = element.parentNode.getElementsByClassName("points")[0].innerText;
    current = Math.max(parseInt(current) - 1, 0);
    element.parentNode.getElementsByClassName("points")[0].innerText = current;
}

document.addEventListener("DOMContentLoaded", function () {
    const results = document.getElementById("results-div");

    if (sessionStorage.getItem("results") !== null) {
        results.innerHTML = sessionStorage.getItem("results");
    }
    else {
        results.innerHTML = document.getElementById('results-template').innerHTML;
        console.log(results.outerHTML)
    }
    sessionStorage.setItem("results", results.innerHTML);

    const observer = new MutationObserver(function (mutationsList, observer) {
        sessionStorage.setItem("results", results.innerHTML);
    });
    observer.observe(results, {attributes: true, childList: true, subtree: true, characterData: true});

    for(let playerField of document.getElementsByClassName('form-control user-field player-field')){
        playerField.onchange = function (value){
            playerField.outerHTML = playerField.outerHTML.replace(/value=".*"/, 'value="'+playerField.value+'"');
        };
    }

    let time = parseInt(sessionStorage.getItem("time"));
    if(isNaN(time)) time = 10;

    const timeRange = document.getElementById('time-range');
    timeRange.value = time;
    document.getElementById('time-range-out').innerText = timeRange.value;
    timeRange.addEventListener('change', function(){
        document.getElementById('time-range-out').innerText = timeRange.value;
        sessionStorage['time'] = timeRange.value;
    });
});

function initColorMode() {
    let mode = sessionStorage.getItem("color-mode");
    if (mode === null) {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
            mode = "dark";
    }

    if (mode === "dark")
        _setDarkMode();
}

function _setLightMode() {
    const body = document.getElementsByTagName("body")[0];
    const nav = document.getElementsByTagName("nav")[0];
    const footer = document.getElementsByTagName("footer")[0];
    const button = document.getElementById("mode-switch");

    body.classList.remove("bg-dark");
    body.classList.remove("text-light");
    nav.classList.remove("bg-dark");
    nav.classList.remove("navbar-dark");
    nav.classList.add("bg-light");
    nav.classList.add("navbar-light");
    footer.classList.add("bg-light");

    for (const li of document.querySelectorAll("li.list-group-item"))
        li.classList.remove("bg-dark");

    button.innerText = "Dark mode";
    sessionStorage.setItem("color-mode", "light");
}

function _setDarkMode() {
    const body = document.getElementsByTagName("body")[0];
    const nav = document.getElementsByTagName("nav")[0];
    const footer = document.getElementsByTagName("footer")[0];
    const button = document.getElementById("mode-switch");

    body.classList.add("bg-dark");
    body.classList.add("text-light");
    nav.classList.add("bg-dark");
    nav.classList.add("navbar-dark");
    footer.classList.remove("bg-light");

    for (const li of document.querySelectorAll("li.list-group-item"))
        li.classList.add("bg-dark");

    button.innerText = "Light mode";
    sessionStorage.setItem("color-mode", "dark");
}

function colorModeSwitch() {
    const body = document.getElementsByTagName("body")[0];

    if (body.className === "bg-dark text-light") {
        _setLightMode();
    } else {
        _setDarkMode();
    }
}
