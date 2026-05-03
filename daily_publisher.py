import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Crush Your Limits: Unleash Your Inner Beast 🦁",
        "The Only Bad Workout Is The One That Didn't Happen 💥",
        "Rise and Grind: Success Starts With Discipline 📈",
        "No Excuses: Your Future Self Will Thank You 🔥",
        "Mindset of a Champion: Conquer Your Day 🏆",
        "Transformation Starts Now: Push Beyond Your Limits 🚀",
        "Consistency is Key: Stay Focused, Stay Strong 💪",
        "Level Up Your Life: The Grind Never Stops ⚡",
        "Fuel Your Ambition: Chase Your Greatness 🌟",
        "Break Your Barriers: Stronger Every Single Day 🔥",
        "Focus on the Goal, Not the Pain 🎯",
        "Unstoppable Energy: Keep Moving Forward 🏃‍♂️",
        "Your Journey, Your Rules: Make it Count! ✨",
        "Built, Not Bought: Earn Your Results 🛠️",
        "Wake Up. Work Out. Kick Ass. Repeat. 🔁",
    ]

    fallback_descriptions = [
        "Stop waiting for the perfect moment—create it! 💥 Success isn't given, it's earned every single day through sweat and discipline. Whether you're just starting or you're miles into your journey, keep pushing forward. Your future self is counting on you! 🚀 If you're ready to crush your goals, hit that SUBSCRIBE button for your daily dose of fuel! 💪🔥 #fitness #motivation #gym #workout #mindset #discipline #success #shorts #reels",
        "The pain you feel today will be the strength you feel tomorrow. 🦁 Don't let excuses hold you back from the greatness you're capable of. It’s time to level up and show the world what you’re made of! Drop a 'YES' in the comments if you're training today! 🏆✨ #fitness #motivation #gym #workout #mindset #discipline #success #shorts #reels",
        "Consistency is the bridge between goals and accomplishment. 📈 Even when you don't feel like it, show up for yourself. Small wins every day lead to massive results. Join our community of champions and let's grow together! 🌟 Like and share with someone who needs this today! 💪💚 #fitness #motivation #gym #workout #mindset #discipline #success #shorts #reels",
        "Transformation is a marathon, not a sprint. 🏃‍♂️ Stay focused on the vision, embrace the grind, and never look back. You are stronger than you think, and more capable than you know. Smash that LIKE button if you're committed to the grind! ⭐ #fitness #motivation #gym #workout #mindset #discipline #success #shorts #reels",
        "Excuses don't burn calories. ⚡ It’s time to stop talking and start doing. Discipline is doing what needs to be done, even when you don’t want to. Your only competition is the person you were yesterday. Follow for daily fitness fire! What's your goal for this month? Comment below! 👇 #fitness #motivation #gym #workout #mindset #discipline #success #shorts #reels",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "high energy and aggressive — focus on pushing limits and crushing goals",
        "disciplined and stoic — capture the mindset of consistency and hard work",
        "inspirational and visionary — highlight the journey of transformation and success",
        "motivational and empowering — show off the strength and ambition needed to win",
        "relentless and gritty — focus on the sweat, the pain, and the ultimate reward",
        "focused and intense — highlight the concentration and mental toughness required",
        "upbeat and energetic — focus on the joy of movement and the post-workout high",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, high-energy, and powerful fitness motivation title and description. "
        f"The content features intense workouts, discipline, and the mindset of a champion. "
        f"Speak as an inspiring fitness coach — energetic, direct, and focused on growth. "
        f"IMPORTANT: Do NOT use generic openers like 'Welcome back' or 'Welcome to our channel'. Start directly with something powerful. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be engaging (3-5 sentences), packed with motivation, and full of personality. "
        f"Include engagement calls-to-action such as: "
        f"- Subscribe for your daily dose of motivation! "
        f"- Comment 'YES' if you're training today! "
        f"- Share this with someone who needs a boost! "
        f"- Smash that LIKE button if you're committed to the grind! "
        f"Include relevant hashtags in ALL LOWERCASE such as #fitness #motivation #gym #workout #mindset #discipline #success #shorts #reels. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["fitness", "motivation", "gym", "workout", "mindset", "discipline", "success", "shorts", "reels"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
