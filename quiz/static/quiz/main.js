Object.defineProperty(HTMLMediaElement.prototype, 'playing', {
    get: function(){
        return !!(this.currentTime > 0 && !this.paused && !this.ended && this.readyState > 2);
    }
})

function addUser() {
    document.getElementById("addUserBtn").insertAdjacentHTML('beforebegin',
        '<div class="input-group"><input type="text" class="form-control" id="user" name="user" required>\n' +
        '                        <button class="btn" type="button"\n' +
        '                            onclick="removeUser(this)">X</button></div>')
}

function removeUser(element) {
    element.parentNode.parentNode.removeChild(element.parentNode)
}

document.addEventListener("DOMContentLoaded", function() {
    const count = document.getElementById('count');
    const details = document.getElementById('details');
    const player = document.getElementById('player')

    let time = 9;
    let waiting = false; // True when waiting for data.

    function play() {
        player.removeEventListener('canplaythrough', play);

        function step() {
            if (time > 0) {
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
            setTimeout(step, 1000);
        }).catch(() => {
            count.innerText = "Enable Autoplay (in the address bar) and press Play!";
       });
    }


    player.addEventListener('canplaythrough', play);
    player.addEventListener('ended', () => { location.reload(); });
    player.addEventListener('waiting', () => { waiting = true; })
    player.addEventListener('playing', () => { waiting = false; })
});

function addPlayer(element){
    li = document.createElement("li");
    li.className = "list-group-item"
    li.innerHTML = '<div class="input-group">\n' +
        '                        <button class="btn" type="button" onclick="removePlayer(this)">X</button>\n' +
        '                        <input type="text" class="form-control user-field" id="user">\n' +
        '                        <button class="btn" type="button" onclick="addPoint(this)">+</button>\n' +
        '                        <button class="btn" type="button" onclick="removePoint(this)">-</button>\n' +
        '                        <div id="points">0</div>' +
        '                    </div>';
    element.parentNode.getElementsByClassName("list-group")[0].appendChild(li);
}

function removePlayer(element){
    element.parentNode.parentNode.parentNode.removeChild(element.parentNode.parentNode)
}

function clearPlayer(element){
    sessionStorage.removeItem('results');
    element.parentNode.getElementsByTagName('div')[0].innerHTML = document.getElementById('results-template').innerHTML;
}

function addPoint(element){
    current = element.parentNode.getElementsByTagName("div")[0].innerText;
    current = parseInt(current) + 1;
    element.parentNode.getElementsByTagName("div")[0].innerText = current;
}

function removePoint(element){
    current = element.parentNode.getElementsByTagName("div")[0].innerText;
    current = Math.max(parseInt(current) - 1, 0);
    element.parentNode.getElementsByTagName("div")[0].innerText = current;
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
});
