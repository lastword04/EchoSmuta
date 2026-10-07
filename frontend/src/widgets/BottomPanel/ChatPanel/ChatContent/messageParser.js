// widgets/ChatPanel/ChatContent/messageParser.js

export const parseSmileys = (text) => {
  const smileyRegex = /\|(\d+)\|/g;
  const matches = [];
  let match;
  
  while ((match = smileyRegex.exec(text)) !== null) {
    matches.push({
      index: match.index,
      fullMatch: match[0],
      smileyNumber: match[1],
    });
  }
  
  return matches;
};

export const parseMentions = (text) => {
  const mentionRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  const matches = [];
  let match;
  
  while ((match = mentionRegex.exec(text)) !== null) {
    matches.push({
      index: match.index,
      fullMatch: match[0],
      name: match[1],
      id: match[2],
    });
  }
  
  return matches;
};

export const parseUrls = (text) => {  
  const urlPattern = /(?:(?:https?|ftp):\/\/|www\.|(?=\S+\.\S+))[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:[^\s]*)/gi;
  const matches = [];
  let match;
  
  while ((match = urlPattern.exec(text)) !== null) {
    matches.push({
      index: match.index,
      fullMatch: match[0],
      url: match[0],
    });
  }
  
  return matches;
};

export const isYouTube = (url) => {
  const youtubeDomains = ['youtube.com', 'youtu.be'];
  try {
    const parsedUrl = new URL(url.startsWith('http') ? url : `https://${url}`);
    const host = parsedUrl.hostname.toLowerCase();
    return youtubeDomains.some(
      (allowed) => host === allowed || host.endsWith(`.${allowed}`)
    );
  } catch {
    return false;
  }
};