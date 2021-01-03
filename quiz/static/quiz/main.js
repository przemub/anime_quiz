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
        function step() {
            if (time > 0) {
                if (!waiting)
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

        player.play();
        count.innerText = time.toString();
        setTimeout(step, 1000);
    }


    player.addEventListener('canplaythrough', play);
    player.addEventListener('ended', () => { location.reload(); });
    player.addEventListener('waiting', () => { waiting = true; })
    player.addEventListener('playing', () => { waiting = false; })
});
