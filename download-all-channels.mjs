#!/usr/bin/env node
// Download all tracks from 3 Suno workspaces
// Auto-fetched via /api/project/me + /api/project/{id}
import { mkdirSync, writeFileSync, statSync } from 'fs';
import { execSync } from 'child_process';

const JWT = execSync('cat /workspace/suno-jwt.txt').toString().trim();
const HEADERS = `-H "Authorization: Bearer ${JWT}" -H "User-Agent: Mozilla/5.0"`;

console.log(`[${new Date().toISOString().slice(11,19)}] Fetching projects...`);

const projectsJson = JSON.parse(execSync(`curl -sS https://studio-api-prod.suno.com/api/project/me ${HEADERS}`).toString());
console.log(`Found ${projectsJson.num_total_results} projects\n`);

const TARGET_PROJECTS = {
    'Fly Chill': '7b661a9c-107a-4297-b0ee-2fa015e66d8b',
    'Lofi Nippon': '2f6a96be-2327-4b87-baec-d21466d6d3c5',
    'TheLoFi': '78136c59-6637-4eea-beba-9582e58b028d',
};

const results = {};

for (const [name, id] of Object.entries(TARGET_PROJECTS)) {
    console.log(`\n=== ${name} (${id}) ===`);
    const projJson = JSON.parse(execSync(
        `curl -sS https://studio-api-prod.suno.com/api/project/${id} ${HEADERS}`
    ).toString());
    
    const dir = `/workspace/tracks-${name.toLowerCase().replace(/\s+/g, '-')}-v3`;
    mkdirSync(dir, { recursive: true });
    
    const clips = projJson.project_clips || [];
    const metadata = [];
    
    for (let i = 0; i < clips.length; i++) {
        const c = clips[i].clip;
        const title = c.title || 'untitled';
        const safeTitle = title.toLowerCase().replace(/[^a-z0-9-]/g, '-').slice(0, 40);
        const filename = `${String(i+1).padStart(2, '0')}-${safeTitle}.mp3`;
        const filepath = `${dir}/${filename}`;
        const dur = c.metadata?.duration || 0;
        
        // Download
        try {
            execSync(`curl -sL -o "${filepath}" "${c.audio_url}"`, { timeout: 120000, stdio: 'ignore' });
            const size = statSync(filepath).size;
            console.log(`  [${String(i+1).padStart(2)}/${clips.length}] ✓ ${title.slice(0,40).padEnd(40)} ${dur.toFixed(1)}s ${(size/1024).toFixed(0)}KB`);
            
            metadata.push({
                index: i + 1,
                title,
                duration: dur,
                audio_url: c.audio_url,
                clip_id: c.id,
                file: filepath,
                size_bytes: size,
            });
        } catch (e) {
            console.log(`  [${i+1}/${clips.length}] ✗ ${title}: ${e.message?.slice(0,80)}`);
        }
    }
    
    results[name] = {
        project_id: id,
        clip_count: clips.length,
        total_duration: metadata.reduce((a, b) => a + b.duration, 0),
        clips: metadata,
    };
    
    writeFileSync(`${dir}/_metadata.json`, JSON.stringify(results[name], null, 2));
}

writeFileSync('/workspace/all-channels-pipeline/_all-downloads.json', JSON.stringify(results, null, 2));

console.log(`\n=== Summary ===`);
for (const [name, data] of Object.entries(results)) {
    const totalDur = data.total_duration;
    const loops2 = totalDur * 2;
    const loops3 = totalDur * 3;
    console.log(`  ${name}: ${data.clip_count} tracks, ${totalDur.toFixed(0)}s raw`);
    console.log(`    2 loops = ${loops2.toFixed(0)}s (${(loops2/60).toFixed(1)} min)`);
    console.log(`    3 loops = ${loops3.toFixed(0)}s (${(loops3/60).toFixed(1)} min)`);
}
