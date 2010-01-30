import webbrowser, urllib

def search_websites(searchurl, doc):
  def search_fn(ensoapi, query=None):
    if not query:
      query = ensoapi.get_selection()["text"]
    if not query:
      ensoapi.display_message("No text selected")
      return 
    esc = urllib.quote_plus(query.encode("utf-8"))
    webbrowser.open(searchurl % esc)
  search_fn.__doc__ = doc  
  return search_fn

cmd_youtube = search_websites("http://www.youtube.com/results?search_query=%s",
  "Searches YouTube")

cmd_wikipedia = search_websites("http://en.wikipedia.org/wiki/Special:Search?search=%s", "Searches Wikipedia")

cmd_unicode = search_websites("http://www.fileformat.info/info/unicode/char/search.htm?q=%s&preview=entity", "Search Unicode character definitions")

cmd_define = search_websites("http://freedictionary.org/?Query=%s", "Defines a word")

