import Parser from 'rss-parser';

const parser = new Parser();

export async function fetchLatestRateNews() {
  try {
    const feed = await parser.parseURL('https://www.mortgagenewsdaily.com/rss/rates');
    // The feed items usually have title, link, content, pubDate, guid
    // Sort by pubDate descending just in case
    const items = feed.items.sort((a, b) => {
      return new Date(b.pubDate || '').getTime() - new Date(a.pubDate || '').getTime();
    });
    
    return items[0];
  } catch (error) {
    console.error("Error fetching RSS feed:", error);
    return null;
  }
}
