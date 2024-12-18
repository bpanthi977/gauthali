let server_time_diff = 0;
let server_time_updates = 0;

function sync_time(t0, t1, t3) {
    const diff = t1 - (t0 + t3) / 2; // if diff is added to local time, we get server time
    if (server_time_updates  == 0) {
        server_time_diff = diff;
    } else {
        const alpha = 0.9; // EMA
        server_time_diff = alpha * server_time_diff + (1 - alpha) * diff;
    }
    server_time_updates++;
}

function update_song_name(name) {
    const song_name = document.getElementById("song-name");
    song_name.innerHTML = name;
}


let diff_lag_ema = 0;
let diff_update_count = 0;

function sync_diff_update(diff) {
    if (diff > 1) {
        diff_lag_ema = 0;
        diff_update_count = 0;
    }


    diff_update_count++;
    if (diff_update_count == 1) { // One diff update give no diff lag info
        diff_lag_ema = 0;
    } else if (diff_update_count == 2) { // Second diff is the diff lag
        diff_lag_ema = diff;
    } else { // After the second take exponential moving average
        const alpha = 0.6;
        diff_lag_ema = alpha * diff_lag_ema + (1 - alpha) * diff;
    }
}

function update_song_time(start_time) {
    const audio = document.getElementById("audio");
    if (audio.paused) return;
    if (start_time == false) {
        audio.currentTime = 0;
        audio.pause();
    } else {
        let time = (Date.now() + server_time_diff - start_time) / 1000;
        if (audio.duration) {
            time = time % audio.duration;
        }
        const diff = time - audio.currentTime;
        console.log({time, start_time, now: Date.now(), d: audio.duration, current: audio.currentTime, diff});
        if (Math.abs(diff) > 0.1) {
            if (audio.duration) {
                sync_diff_update(diff);
            }
            console.log({diff, diff_lag_ema, diff_update_count, d: diff + diff_lag_ema});
            audio.currentTime = time + diff_lag_ema;
            audio.play();
        }
    }
}

function update_song(id) {
    const audioSource = document.getElementById("audio-source");
    const audio = document.getElementById("audio");
    const prev_id = audio.getAttribute('data-id')
    if (id != 0 && prev_id != id) {
        audioSource.src = '/music?#' + id;
        audio.load();
        audio.setAttribute('data-id', id);
        audio.play();
    }
}

async function update_state() {
    const t0 = Date.now();

    const result = await (await fetch('/state')).json();
    const {filename, start_time, id, server_time} = result;

    const t3 = Date.now();
    sync_time(t0, server_time, t3);

    if (filename) {
        update_song(id);
        update_song_name(filename);
        update_song_time(start_time);
    } else {
        update_song_name('Nothing');
        update_song_time(false);
    }
}

function update_time() {
    const audio = document.getElementById("audio");
    const time = document.getElementById("time");
    if (!time) return;
    const date = new Date();
    date.setUTCMilliseconds(date.getUTCMilliseconds() + server_time_diff);
    time.innerHTML =  date + `[ diff: ${server_time_diff.toFixed(0)} ms (${server_time_updates})]`;
    time.innerHTML += `\n [seek time: ${audio.currentTime}]`;
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("Setting interval");
    setInterval(update_state, 1000);
    setInterval(update_time, 200);
});
