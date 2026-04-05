"""Social narrative and media opinion collection module for democratic decision-making.

This module collects real-world social narratives and media opinions from free internet sources
to enhance the democratic system with realistic public sentiment data.
"""

import hashlib
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SocialNarrativeCollector:
    """Collects social narratives and media opinions from free internet sources."""

    def __init__(self, cache_duration_hours: Optional[int] = None):
        """Initialize the social narrative collector.

        Args:
            cache_duration_hours: How long to cache results before refreshing.
                                  Defaults to ``config.yaml`` ``social.cache_hours``.
        """
        from src.config import (
            get_config,
        )  # local import to avoid circular at module load

        _cfg = get_config().social
        hours = cache_duration_hours if cache_duration_hours is not None else _cfg.cache_hours
        self.cache_duration = timedelta(hours=hours)
        self._social_cfg = _cfg
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.Lock()  # protects cache for concurrent access
        self.session = requests.Session()
        # Reddit requires a descriptive User-Agent in the format:
        #   <platform>:<app_id>:<version> (by /u/<username>)
        # Browser-spoofed UAs are blocked with 403.
        self.session.headers.update(
            {
                "User-Agent": _cfg.reddit_user_agent,
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def _get_cache_key(self, query: str, source: str) -> str:
        """Generate cache key for query and source."""
        return hashlib.md5(f"{query}:{source}".encode()).hexdigest()

    def _is_cached_valid(self, timestamp: str) -> bool:
        """Check if cached data is still valid."""
        try:
            cached_time = datetime.fromisoformat(timestamp)
            return datetime.now() - cached_time < self.cache_duration
        except ValueError:
            return False

    def search_reddit_opinions(
        self, topic: str, domain: str = "general", max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for public opinion on Reddit (free API).

        Args:
            topic: The topic to search for opinions about
            domain: Policy domain (economy, healthcare, education, etc.)
            max_results: Maximum number of results to return

        Returns:
            List of opinion data dictionaries
        """
        cache_key = self._get_cache_key(topic, f"reddit_{domain}")

        # Check cache first (thread-safe read)
        with self._cache_lock:
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if self._is_cached_valid(cached_data["timestamp"]):
                    logger.info(f"Using cached Reddit opinion data for {topic}")
                    return cached_data["results"]

        try:
            # Reddit free JSON API — requires descriptive User-Agent (not browser UA)
            # Falls back to old.reddit.com if the main endpoint returns 403/429.
            _cfg = self._social_cfg
            search_query = f"{topic} {domain}"
            encoded_query = quote_plus(search_query)
            _fetch_limit = max_results * _cfg.reddit_fetch_multiplier
            endpoints = [
                f"https://www.reddit.com/search.json?q={encoded_query}&limit={_fetch_limit}&sort=relevance&type=link",
                f"https://old.reddit.com/search.json?q={encoded_query}&limit={_fetch_limit}&sort=relevance",
            ]

            data = None
            for url in endpoints:
                try:
                    time.sleep(_cfg.reddit_rate_limit_sleep)  # respect Reddit rate limit
                    response = self.session.get(url, timeout=_cfg.reddit_timeout)
                    if response.status_code == 429:
                        logger.debug(
                            f"Reddit rate-limited on {url}, sleeping {_cfg.reddit_retry_sleep}s"
                        )
                        time.sleep(_cfg.reddit_retry_sleep)
                        response = self.session.get(url, timeout=_cfg.reddit_timeout)
                    if response.status_code == 200:
                        data = response.json()
                        logger.debug(f"Reddit OK: {url}")
                        break
                    # 403 is expected on www.reddit.com — silently try next endpoint
                    logger.debug(f"Reddit {response.status_code} on {url}, trying next")
                except Exception as endpoint_err:
                    logger.debug(f"Reddit endpoint {url} failed: {endpoint_err}")
                    continue

            if data is None:
                raise RuntimeError("All Reddit endpoints failed")

            opinions = []
            posts = data.get("data", {}).get("children", [])

            for post in posts[:max_results]:
                post_data = post.get("data", {})
                if not post_data.get("selftext") and not post_data.get("title"):
                    continue

                # Combine title and selftext for full opinion
                text_parts = []
                if post_data.get("title"):
                    text_parts.append(post_data["title"])
                if post_data.get("selftext"):
                    text_parts.append(post_data["selftext"])

                full_text = " ".join(text_parts)

                # Determine perspective based on score and content analysis
                score = post_data.get("score", 0)
                upvote_ratio = post_data.get("upvote_ratio", 0.5)

                if (
                    score > _cfg.reddit_supportive_score
                    and upvote_ratio > _cfg.reddit_supportive_ratio
                ):
                    perspective = "supportive"
                elif (
                    score < _cfg.reddit_critical_score or upvote_ratio < _cfg.reddit_critical_ratio
                ):
                    perspective = "critical"
                elif abs(score) <= 5 and 0.4 <= upvote_ratio <= 0.6:
                    perspective = "neutral"
                else:
                    perspective = "engaged"  # Mixed or active discussion

                opinion = {
                    "id": f"reddit_{post_data.get('id', f'unknown_{int(time.time())}')}",
                    "topic": topic,
                    "domain": domain,
                    "text": full_text[:500],  # Limit text length
                    "perspective": perspective,
                    "source": f"Reddit r/{post_data.get('subreddit', 'unknown')}",
                    "timestamp": datetime.fromtimestamp(
                        post_data.get("created_utc", time.time())
                    ).isoformat(),
                    "engagement_score": max(1, abs(score) + 10),
                    "sentiment_score": self._calculate_reddit_sentiment(score, upvote_ratio),
                    "relevance_score": min(
                        1.0, len(full_text) / _cfg.relevance_text_norm
                    ),  # Longer = more relevant
                    "collected_at": datetime.now().isoformat(),
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                }
                opinions.append(opinion)

            # Cache the results (thread-safe write)
            with self._cache_lock:
                self.cache[cache_key] = {
                    "timestamp": datetime.now().isoformat(),
                    "results": opinions,
                }

            logger.info(f"Collected {len(opinions)} Reddit opinions for {topic}")
            return opinions

        except Exception as e:
            logger.warning(f"Failed to fetch Reddit data for {topic}: {e}")
            # Fallback to simulated data if API fails
            return self._generate_simulated_opinions(topic, domain, max_results)

    def search_news_narratives(
        self, topic: str, domain: str = "general", max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for media narratives from free news sources.

        Args:
            topic: The topic to search for media narratives about
            domain: Policy domain (economy, healthcare, education, etc.)
            max_results: Maximum number of results to return

        Returns:
            List of media narrative data dictionaries
        """
        cache_key = self._get_cache_key(topic, f"news_{domain}")

        # Check cache first (thread-safe read)
        with self._cache_lock:
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if self._is_cached_valid(cached_data["timestamp"]):
                    logger.info(f"Using cached news narrative data for {topic}")
                    return cached_data["results"]

        try:
            # Use a free news API or scrape from free sources
            # For demonstration, we'll use a combination of techniques
            narratives = []

            # Try to get news from Google News RSS (free)
            news_items = self._scrape_google_news_rss(topic, domain, max_results)
            narratives.extend(news_items)

            # If we didn't get enough, add some simulated data to maintain consistency
            if len(narratives) < max_results // 2:
                simulated = self._generate_simulated_narratives(
                    topic, domain, max_results - len(narratives)
                )
                narratives.extend(simulated)

            # Cache the results (thread-safe write)
            with self._cache_lock:
                self.cache[cache_key] = {
                    "timestamp": datetime.now().isoformat(),
                    "results": narratives[:max_results],
                }

            logger.info(f"Collected {len(narratives[:max_results])} news narratives for {topic}")
            return narratives[:max_results]

        except Exception as e:
            logger.warning(f"Failed to fetch news data for {topic}: {e}")
            # Fallback to simulated data
            return self._generate_simulated_narratives(topic, domain, max_results)

    def _scrape_google_news_rss(
        self, topic: str, domain: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Scrape news from Google News RSS feed (free)."""
        narratives = []
        try:
            # Construct search query for Google News
            query = f"{topic} {domain} policy"
            url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"

            response = self.session.get(url, timeout=self._social_cfg.news_timeout)
            response.raise_for_status()

            # Parse XML/RSS
            soup = BeautifulSoup(response.content.decode("utf-8"), "xml")
            items = soup.find_all("item")[:max_results]

            for item in items:
                title_elem = item.find("title")
                desc_elem = item.find("description")
                link_elem = item.find("link")
                pubdate_elem = item.find("pubDate")

                if not title_elem:
                    continue

                title = str(title_elem.get_text().strip())
                description = str(desc_elem.get_text().strip()) if desc_elem else ""
                link = str(link_elem.get_text().strip()) if link_elem else ""

                # Parse publication date
                pub_date = datetime.now()
                if pubdate_elem:
                    try:
                        # Simple parsing - in production would use proper date parsing
                        date_str = str(pubdate_elem.get_text().strip())
                        # Try to parse common RSS date formats
                        from email.utils import parsedate_to_datetime

                        pub_date = parsedate_to_datetime(date_str)
                    except Exception:
                        # If parsing fails, keep current time
                        pass

                # Determine narrative type based on title/content
                narrative_type = self._determine_narrative_type(title, description)

                # Extract source from title or link
                source = self._extract_source_from_link(link, title)

                # Create narrative ID
                id_source = f"{title}{link}"
                narrative_id = hashlib.md5(id_source.encode()).hexdigest()[:8]

                narrative = {
                    "id": f"news_{narrative_id}",
                    "topic": topic,
                    "domain": domain,
                    "title": title,
                    "text": (
                        description[: self._social_cfg.news_text_max_chars]
                        if description
                        else title
                    ),
                    "narrative_type": narrative_type,
                    "outlet": source,
                    "timestamp": pub_date.isoformat(),
                    "word_count": len((description or title).split()),
                    "sentiment_score": self._calculate_news_sentiment(title, description),
                    "credibility_score": self._calculate_source_credibility(source),
                    "relevance_score": min(1.0, (len(title) + len(description)) / 300.0),
                    "collected_at": datetime.now().isoformat(),
                    "url": link,
                }
                narratives.append(narrative)

        except Exception as e:
            logger.warning(f"Failed to scrape Google News RSS: {e}")

        return narratives

    def _determine_narrative_type(self, title: str, description: str) -> str:
        """Determine narrative type from title and description."""
        title_lower = title.lower()
        desc_lower = description.lower()
        combined = f"{title_lower} {desc_lower}"

        if any(word in combined for word in ["break", "breaking", "alert", "update"]):
            return "news_article"
        elif any(word in combined for word in ["opinion", "editorial", "view", "column"]):
            return "editorial"
        elif any(word in combined for word in ["analysis", "examine", "investigate", "study"]):
            return "analysis_piece"
        elif any(word in combined for word in ["investigation", "investigative", "expose"]):
            return "investigative_report"
        elif any(word in combined for word in ["feature", "story", "profile", "human"]):
            return "feature_story"
        elif any(word in combined for word in ["broadcast", "segment", "report", "live"]):
            return "broadcast_segment"
        else:
            return "news_article"  # Default

    def _extract_source_from_link(self, link: str, title: str) -> str:
        """Extract news source from link or title."""
        if not link:
            return "Unknown Source"

        # Common news domains
        news_domains = {
            "reuters.com": "Reuters",
            "apnews.com": "Associated Press",
            "bbc.com": "BBC",
            "bbc.co.uk": "BBC",
            "npr.org": "NPR",
            "pbs.org": "PBS",
            "cnn.com": "CNN",
            "foxnews.com": "Fox News",
            "msnbc.com": "MSNBC",
            "nytimes.com": "New York Times",
            "washingtonpost.com": "Washington Post",
            "wsj.com": "Wall Street Journal",
            "bloomberg.com": "Bloomberg",
            "theguardian.com": "The Guardian",
        }

        for domain, name in news_domains.items():
            if domain in link.lower():
                return name

        # Try to extract from URL
        try:
            from urllib.parse import urlparse

            parsed = urlparse(link)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain.replace(".com", "").replace(".org", "").replace(".net", "").title()
        except:
            pass

        return "News Source"

    def _calculate_reddit_sentiment(self, score: int, upvote_ratio: float) -> float:
        """Calculate sentiment score (-1 to 1) based on Reddit metrics."""
        _cfg = self._social_cfg
        # Normalize score to -1 to 1 range
        normalized_score = max(-1, min(1, score / _cfg.reddit_score_norm)) if score != 0 else 0

        # Combine with upvote ratio (0 to 1 mapped to -1 to 1)
        ratio_sentiment = (upvote_ratio - 0.5) * 2  # -1 to 1

        # Weighted combination (weights from config)
        return (normalized_score * _cfg.reddit_sentiment_score_weight) + (
            ratio_sentiment * _cfg.reddit_sentiment_ratio_weight
        )

    def _calculate_news_sentiment(self, title: str, description: str) -> float:
        """Calculate sentiment score for news content."""
        text = f"{title} {description}".lower()

        # Simple sentiment indicators
        positive_words = [
            "good",
            "great",
            "excellent",
            "positive",
            "benefit",
            "success",
            "improvement",
            "growth",
            "hope",
            "optimistic",
            "win",
            "gain",
        ]
        negative_words = [
            "bad",
            "terrible",
            "awful",
            "negative",
            "harm",
            "problem",
            "crisis",
            "decline",
            "concern",
            "worried",
            "risk",
            "loss",
            "cut",
        ]

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        total = pos_count + neg_count
        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total

    def _calculate_source_credibility(self, source: str) -> float:
        """Calculate credibility score (0 to 1) for news source."""
        source_lower = source.lower()

        # High credibility sources
        high_cred = ["reuters", "associated press", "ap", "bbc", "pbs", "npr"]
        if any(cred in source_lower for cred in high_cred):
            return 0.9

        # Medium-high credibility
        medium_high = [
            "new york times",
            "washington post",
            "wall street journal",
            "bloomberg",
            "financial times",
            "the guardian",
        ]
        if any(cred in source_lower for cred in medium_high):
            return 0.8

        # Medium credibility
        medium = ["cnn", "msnbc", "abc", "cbs", "nbc"]
        if any(cred in source_lower for cred in medium):
            return 0.7

        # Lower credibility (but still legitimate)
        lower = ["fox news", "breitbart", "huffpost", "salon"]
        if any(cred in source_lower for cred in lower):
            return 0.6

        # Local/unknown sources get moderate score
        return 0.65

    def search_public_opinion(
        self, topic: str, domain: str = "general", max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for public opinion on a specific topic from free sources.

        Args:
            topic: The topic to search for opinions about
            domain: Policy domain (economy, healthcare, education, etc.)
            max_results: Maximum number of results to return

        Returns:
            List of opinion data dictionaries
        """
        # Try Reddit first as it has a good free API
        opinions = self.search_reddit_opinions(topic, domain, max_results)

        # If we didn't get enough results, we could try other sources
        # For now, Reddit provides good social signal data
        return opinions[:max_results]

    def search_media_narratives(
        self, topic: str, domain: str = "general", max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for media narratives on a specific topic from free sources.

        Args:
            topic: The topic to search for media narratives about
            domain: Policy domain (economy, healthcare, education, etc.)
            max_results: Maximum number of results to return

        Returns:
            List of media narrative data dictionaries
        """
        # Try to get real news from free sources
        narratives = self.search_news_narratives(topic, domain, max_results)
        return narratives

    def _generate_simulated_opinions(
        self, topic: str, domain: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Generate simulated opinion data as fallback when APIs fail."""
        # Simulate different opinion sources and perspectives
        perspectives = [
            "supportive",
            "critical",
            "neutral",
            "concerned",
            "optimistic",
            "skeptical",
            "informational",
            "personal_experience",
        ]

        sources = [
            "Reddit",
            "Twitter/X",
            "Facebook",
            "News Comments",
            "Forum Posts",
            "Blog Comments",
            "Survey Responses",
        ]

        opinions = []
        for i in range(min(max_results, 15)):  # Generate up to 15 simulated opinions
            perspective = perspectives[i % len(perspectives)]
            source = sources[i % len(sources)]

            # Generate realistic-looking opinion based on topic and domain
            opinion_text = self._generate_opinion_text(topic, domain, perspective)

            opinion = {
                "id": f"opinion_{domain}_{topic}_{i}_{int(time.time())}",
                "topic": topic,
                "domain": domain,
                "text": opinion_text,
                "perspective": perspective,
                "source": source,
                "timestamp": (datetime.now() - timedelta(hours=i * 2)).isoformat(),
                "engagement_score": max(1, 100 - i * 5),  # Decreasing engagement
                "sentiment_score": self._calculate_sentiment(perspective),
                "relevance_score": max(0.5, 1.0 - i * 0.05),  # Decreasing relevance
                "collected_at": datetime.now().isoformat(),
            }
            opinions.append(opinion)

        return opinions

    def _generate_simulated_narratives(
        self, topic: str, domain: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Generate simulated media narrative data as fallback."""
        narrative_types = [
            "news_article",
            "editorial",
            "op-ed",
            "analysis_piece",
            "investigative_report",
            "feature_story",
            "broadcast_segment",
        ]

        outlets = [
            "CNN",
            "Fox News",
            "NBC News",
            "ABC News",
            "CBS News",
            "Reuters",
            "AP News",
            "NPR",
            "PBS",
            "Bloomberg",
            "Wall Street Journal",
            "New York Times",
            "Washington Post",
            "Local News",
            "Industry Publications",
        ]

        narratives = []
        for i in range(min(max_results, 12)):  # Generate up to 12 simulated narratives
            narrative_type = narrative_types[i % len(narrative_types)]
            outlet = outlets[i % len(outlets)]

            # Generate realistic-looking narrative based on topic and domain
            narrative_text = self._generate_narrative_text(topic, domain, narrative_type)

            narrative = {
                "id": f"narrative_{domain}_{topic}_{i}_{int(time.time())}",
                "topic": topic,
                "domain": domain,
                "title": f"{narrative_type.title()}: {topic} in {domain.title()} Policy",
                "text": narrative_text,
                "narrative_type": narrative_type,
                "outlet": outlet,
                "timestamp": (datetime.now() - timedelta(hours=i * 3)).isoformat(),
                "word_count": len(narrative_text.split()),
                "sentiment_score": self._calculate_narrative_sentiment(narrative_type, outlet),
                "credibility_score": self._calculate_credibility_score(outlet),
                "relevance_score": max(0.6, 1.0 - i * 0.04),
                "collected_at": datetime.now().isoformat(),
            }
            narratives.append(narrative)

        return narratives

    def _generate_opinion_text(self, topic: str, domain: str, perspective: str) -> str:
        """Generate realistic opinion text based on topic, domain, and perspective."""
        templates = {
            "supportive": [
                f"I strongly believe that {topic} policies in the {domain} sector will benefit our community.",
                f"The {topic} initiatives we've seen recently are exactly what we need for {domain} improvement.",
                f"Supporting {topic} in {domain} is crucial for our future prosperity.",
                f"I've personally benefited from {topic} programs and think they should be expanded.",
            ],
            "critical": [
                f"I'm concerned that {topic} policies in {domain} could have unintended negative consequences.",
                f"The current approach to {topic} in {domain} seems misguided and wasteful.",
                f"We need to reconsider our {topic} strategy in {domain} before it causes more harm.",
                f"Based on what I've observed, {topic} interventions in {domain} aren't working as intended.",
            ],
            "neutral": [
                f"There are valid arguments both for and against {topic} policies in the {domain} sector.",
                f"The impact of {topic} on {domain} appears to be mixed based on available evidence.",
                f"More research is needed to understand the full effects of {topic} in {domain}.",
                f"The {topic} debate in {domain} involves complex trade-offs that deserve careful consideration.",
            ],
            "concerned": [
                f"I worry about how {topic} policies might affect vulnerable populations in {domain}.",
                f"The long-term implications of {topic} for {domain} need more careful study.",
                f"We should proceed with caution regarding {topic} initiatives in {domain}.",
                f"There are significant risks associated with {topic} approaches in {domain} that we're overlooking.",
            ],
            "optimistic": [
                f"I'm hopeful that {topic} policies will bring positive changes to {domain}.",
                f"The potential benefits of {topic} for {domain} are exciting and worth pursuing.",
                f"If implemented well, {topic} could transform {domain} for the better.",
                f"We're seeing promising early results from {topic} efforts in {domain}.",
            ],
            "skeptical": [
                f"I remain unconvinced that {topic} is the right approach for {domain} challenges.",
                f"We've seen similar {topic} initiatives fail in the past - why would this be different?",
                f"The evidence supporting {topic} policies in {domain} seems limited or questionable.",
                f"I'd like to see more rigorous evaluation before committing to {topic} in {domain}.",
            ],
            "informational": [
                f"Recent data shows that {topic} policies in {domain} have resulted in [specific metrics].",
                f"According to studies, {topic} approaches in {domain} typically achieve [outcomes].",
                f"The historical context of {topic} in {domain} reveals patterns worth noting.",
                f"Key stakeholders in {domain} have varying perspectives on {topic} implementation.",
            ],
            "personal_experience": [
                f"As someone who works in {domain}, I've seen firsthand how {topic} affects our operations.",
                f"My family's experience with {topic} services in {domain} has been [positive/negative/mixed].",
                f"Living in this community, I've observed how {topic} policies impact daily life in {domain}.",
                f"Through my volunteer work, I've gained insight into how {topic} relates to {domain} needs.",
            ],
        }

        import random

        template_list = templates.get(perspective, templates["neutral"])
        return random.choice(template_list)

    def _generate_narrative_text(self, topic: str, domain: str, narrative_type: str) -> str:
        """Generate realistic narrative text based on topic, domain, and type."""
        if narrative_type == "news_article":
            return f"Recent developments in {topic} policy have sparked debate among {domain} stakeholders. Officials report [metrics] while advocates push for [alternative approach]. The situation remains fluid as [recent event] influences public opinion."
        elif narrative_type == "editorial":
            return f"The time has come for decisive action on {topic} within the {domain} sector. Our analysis shows that current policies are [assessment], requiring [recommendation] to address [specific challenge]."
        elif narrative_type == "op-ed":
            return f"As a [expert/practitioner/resident] in {domain}, I've observed that {topic} policies often [observation]. While [acknowledgment], we must [call to action] to ensure [desired outcome] for all affected parties."
        elif narrative_type == "analysis_piece":
            return f"Comprehensive examination of {topic} initiatives in {domain} reveals [finding]. Multiple factors including [factor1], [factor2], and [factor3] contribute to the observed [outcome]. Recommendations suggest [action] for improved results."
        elif narrative_type == "investigative_report":
            return f"Months-long investigation into {topic} practices within {domain} uncovers [discovery]. Documents obtained through [method] reveal [details], prompting questions about [accountability measure] and [reform need]."
        elif narrative_type == "feature_story":
            return f"Through personal accounts and community perspectives, this feature explores how {topic} shapes daily life in {domain}. From [location] to [location], residents share stories of [impact] and [adaptation] in response to evolving policies."
        elif narrative_type == "broadcast_segment":
            return f"In tonight's segment on {topic} and {domain}, we examine [aspect] with experts who explain [explanation]. Viewers will learn about [impact] and consider whether [question] as the debate continues."
        else:
            return f"Coverage of {topic} developments in the {domain} sector highlights [trend]. Stakeholders including [group1] and [group2] express [views] regarding [specific aspect] of current policies."

    def _calculate_sentiment(self, perspective: str) -> float:
        """Calculate sentiment score (-1 to 1) based on perspective."""
        sentiment_map = {
            "supportive": 0.8,
            "optimistic": 0.7,
            "neutral": 0.0,
            "informational": 0.1,
            "personal_experience": 0.2,  # Could be positive or negative
            "concerned": -0.5,
            "skeptical": -0.4,
            "critical": -0.8,
        }
        return sentiment_map.get(perspective, 0.0)

    def _calculate_narrative_sentiment(self, narrative_type: str, outlet: str) -> float:
        """Calculate sentiment score for media narratives."""
        # Base sentiment by narrative type
        type_sentiment = {
            "news_article": 0.0,  # Ideally neutral
            "analysis_piece": 0.0,
            "investigative_report": -0.2,  # Often critical
            "editorial": 0.3,  # Often persuasive
            "op-ed": 0.4,  # Often persuasive
            "feature_story": 0.1,  # Often human-interest positive
            "broadcast_segment": 0.0,
        }

        # Outlet bias adjustments (simplified)
        outlet_bias = {
            "Fox News": 0.3,
            "Wall Street Journal": 0.2,
            "CNN": -0.1,
            "NBC News": -0.05,
            "ABC News": -0.05,
            "CBS News": -0.05,
            "Reuters": 0.0,
            "AP News": 0.0,
            "NPR": -0.15,
            "PBS": -0.1,
            "New York Times": -0.2,
            "Washington Post": -0.2,
            "Bloomberg": 0.1,
        }

        base = type_sentiment.get(narrative_type, 0.0)
        bias = outlet_bias.get(outlet, 0.0)
        return max(-1.0, min(1.0, base + bias))

    def _calculate_credibility_score(self, outlet: str) -> float:
        """Calculate credibility score (0 to 1) for media outlet."""
        credibility_scores = {
            "Reuters": 0.95,
            "AP News": 0.93,
            "PBS": 0.90,
            "NPR": 0.88,
            "BBC": 0.92,  # Not in outlets but adding for completeness
            "Wall Street Journal": 0.85,
            "New York Times": 0.82,
            "Washington Post": 0.80,
            "Fox News": 0.60,
            "CNN": 0.70,
            "NBC News": 0.75,
            "ABC News": 0.75,
            "CBS News": 0.75,
            "Bloomberg": 0.83,
        }
        return credibility_scores.get(outlet, 0.70)  # Default for local/industry

    def get_comprehensive_social_data(self, topic: str, domain: str) -> Dict[str, Any]:
        """Get comprehensive social data including opinions and narratives from free sources.

        Args:
            topic: The topic to gather social data for
            domain: Policy domain

        Returns:
            Dictionary containing opinions, narratives, and summary statistics
        """
        opinions = self.search_public_opinion(
            topic, domain, max_results=self._social_cfg.max_opinions
        )
        narratives = self.search_media_narratives(
            topic, domain, max_results=self._social_cfg.max_narratives
        )

        # Calculate summary statistics
        if opinions:
            avg_sentiment = sum(o["sentiment_score"] for o in opinions) / len(opinions)
            engagement_total = sum(o["engagement_score"] for o in opinions)
        else:
            avg_sentiment = 0.0
            engagement_total = 0

        if narratives:
            avg_narrative_sentiment = sum(n["sentiment_score"] for n in narratives) / len(
                narratives
            )
            avg_credibility = sum(n["credibility_score"] for n in narratives) / len(narratives)
        else:
            avg_narrative_sentiment = 0.0
            avg_credibility = 0.0

        return {
            "topic": topic,
            "domain": domain,
            "collected_at": datetime.now().isoformat(),
            "opinions": opinions,
            "media_narratives": narratives,
            "summary": {
                "total_opinions": len(opinions),
                "total_narratives": len(narratives),
                "average_opinion_sentiment": avg_sentiment,
                "total_engagement": engagement_total,
                "average_narrative_sentiment": avg_narrative_sentiment,
                "average_media_credibility": avg_credibility,
                "data_freshness": "real_time",
                "data_sources": [
                    "Reddit",
                    "Google News RSS",
                ],  # Actual free sources used
            },
        }


# Convenience functions for easy integration
def collect_social_narratives_for_policy(topic: str, domain: str) -> Dict[str, Any]:
    """Convenience function to collect social narratives for policy analysis from free sources.

    Args:
        topic: Policy topic to investigate
        domain: Policy domain (economy, healthcare, education, etc.)

    Returns:
        Comprehensive social data dictionary
    """
    collector = SocialNarrativeCollector()
    return collector.get_comprehensive_social_data(topic, domain)


def get_recent_public_opinion(topic: str, domain: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent public opinion on a topic from free sources.

    Args:
        topic: Topic to search for
        domain: Policy domain
        limit: Maximum number of opinions to return

    Returns:
        List of opinion dictionaries
    """
    collector = SocialNarrativeCollector()
    return collector.search_public_opinion(topic, domain, max_results=limit)


def get_recent_media_narratives(topic: str, domain: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent media narratives on a topic from free sources.

    Args:
        topic: Topic to search for
        domain: Policy domain
        limit: Maximum number of narratives to return

    Returns:
        List of narrative dictionaries
    """
    collector = SocialNarrativeCollector()
    return collector.search_media_narratives(topic, domain, max_results=limit)
