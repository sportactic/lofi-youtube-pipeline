#!/usr/bin/env python3
"""Upload albums to Google Drive. RUNS WHEN DRIVE OAUTH COMPLETE."""
import os, sys, json, glob
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_creds():
    """Get OAuth credentials"""
    creds = None
    if os.path.exists('/workspace/google-drive-token.json'):
        creds = Credentials.from_authorized_user_file('/workspace/google-drive-token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("ERROR: No valid Drive credentials. Run OAuth first.")
            sys.exit(1)
        
        with open('/workspace/google-drive-token.json', 'w') as f:
            f.write(creds.to_json())
    
    return creds

def get_headers(creds):
    return {'Authorization': f'Bearer {creds.token}'}

def create_folder(name, parent_id=None):
    """Create a Drive folder"""
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_id:
        metadata['parents'] = [parent_id]
    
    resp = requests.post(
        'https://www.googleapis.com/drive/v3/files',
        headers={**get_headers(creds), 'Content-Type': 'application/json'},
        json=metadata,
    )
    return resp.json()['id']

def upload_file(local_path, parent_id, name=None):
    """Upload a file to Drive"""
    if not name:
        name = os.path.basename(local_path)
    
    # Step 1: Create file metadata
    metadata = {
        'name': name,
        'parents': [parent_id],
    }
    
    resp = requests.post(
        'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
        headers=get_headers(creds),
        files={'metadata': (None, json.dumps(metadata), 'application/json')},
        data=open(local_path, 'rb'),
    )
    return resp.json()

def main():
    global creds
    creds = get_creds()
    
    # Create root folder
    print("Creating root folder: LoFi Music Hub")
    root_id = create_folder('LoFi Music Hub')
    
    # Per channel
    for channel in ['thelofi', 'lofinippon', 'flychill']:
        print(f"\n--- {channel} ---")
        ch_id = create_folder('TheLoFi' if channel == 'thelofi' else 'LofiNippon' if channel == 'lofinippon' else 'FlyChill', root_id)
        
        # Per video folder
        for vid_dir in sorted(glob.glob(f'/workspace/distrokid/per-video-albums/{channel}_*/')):
            vid = os.path.basename(vid_dir.rstrip('/'))
            print(f"  Uploading {vid}...")
            
            vid_id = create_folder(vid, ch_id)
            
            # Upload cover
            cover_path = f'{vid_dir}/cover.jpg'
            if os.path.exists(cover_path):
                upload_file(cover_path, vid_id, 'cover.jpg')
            
            # Upload album.json
            json_path = f'{vid_dir}/album.json'
            if os.path.exists(json_path):
                upload_file(json_path, vid_id, 'album.json')
            
            # Upload tracks
            tracks_dir = f'{vid_dir}/tracks'
            for mp3 in sorted(glob.glob(f'{tracks_dir}/*.mp3')):
                name = os.path.basename(mp3)
                upload_file(mp3, vid_id, f'tracks/{name}')
        
        # Master album
        master_dir = f'/workspace/distrokid/albums/{channel}'
        if os.path.exists(master_dir):
            print(f"  Uploading {channel} Master Album...")
            m_id = create_folder(f'{channel} Master Album', ch_id)
            
            cover = f'{master_dir}/cover.jpg'
            if os.path.exists(cover):
                upload_file(cover, m_id, 'cover.jpg')
            
            json_path = f'{master_dir}/album.json'
            if os.path.exists(json_path):
                upload_file(json_path, m_id, 'album.json')
            
            for mp3 in sorted(glob.glob(f'{master_dir}/tracks/*.mp3')):
                name = os.path.basename(mp3)
                upload_file(mp3, m_id, f'tracks/{name}')
    
    print("\n✓ All uploaded!")

if __name__ == '__main__':
    main()
