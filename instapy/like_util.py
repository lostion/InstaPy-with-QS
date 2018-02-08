import re
import random

"""Module that handles the like features"""
from math import ceil
from re import findall
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException

from .time_util import sleep
from .util import update_activity
from .util import add_user_to_blacklist
from .util import quota_supervisor
from .util import click_element


def get_links_from_feed(browser, amount, num_of_search, logger):
    """Fetches random number of links from feed and returns a list of links"""

    browser.get('https://www.instagram.com')
    # update server calls
    update_activity()
    sleep(2)

    for i in range(num_of_search + 1):
        browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        sleep(2)

    # get links
    link_elems = browser.find_elements_by_xpath(
        "//article/div[2]/div[2]/a")

    total_links = len(link_elems)
    logger.info("Total of links feched for analysis: {}".format(total_links))
    links = []
    try:
        if link_elems:
            links = [link_elem.get_attribute('href') for link_elem in link_elems]
            logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            for i, link in enumerate(links):
                print(i, link)
            logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    except BaseException as e:
        logger.error("link_elems error {}".format(str(e)))

    return links


def get_links_for_location(browser,
                           location,
                           amount,
                           logger,
                           media=None,
                           skip_top_posts=True):

    """Fetches the number of links specified
    by amount and returns a list of links"""
    if media is None:
        # All known media types
        media = ['', 'Post', 'Video']
    elif media == 'Photo':
        # Include posts with multiple images in it
        media = ['', 'Post']
    else:
        # Make it an array to use it in the following part
        media = [media]

    browser.get('https://www.instagram.com/explore/locations/' + location)
    # update server calls
    update_activity()
    sleep(2)

    # clicking load more
    body_elem = browser.find_element_by_tag_name('body')
    sleep(2)

    abort = True
    try:
        load_button = body_elem.find_element_by_xpath(
            '//a[contains(@class, "_1cr2e _epyes")]')
    except:
        try:
            # scroll down to load posts
            for i in range(int(ceil(amount/12))):
                browser.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                sleep(2)
        except:
            logger.warning(
                'Load button not found, working with current images!')
        else:
            abort = False
            body_elem.send_keys(Keys.END)
            sleep(2)
            # update server calls
            update_activity()
    else:
        abort = False
        body_elem.send_keys(Keys.END)
        sleep(2)
        click_element(browser, load_button) # load_button.click()
        # update server calls
        update_activity()

    body_elem.send_keys(Keys.HOME)
    sleep(1)

    # Get links
    if skip_top_posts:
        main_elem = browser.find_element_by_xpath('//main/article/div[2]')
    else:
        main_elem = browser.find_element_by_tag_name('main')

    link_elems = main_elem.find_elements_by_tag_name('a')
    total_links = len(link_elems)
    links = [link_elem.get_attribute('href') for link_elem in link_elems
             if link_elem.text in media]
    filtered_links = len(links)

    while (filtered_links < amount) and not abort:
        amount_left = amount - filtered_links
        # Average items of the right media per page loaded
        new_per_page = ceil(12 * filtered_links / total_links)
        if new_per_page == 0:
            # Avoid division by zero
            new_per_page = 1. / 12.
        # Number of page load needed
        new_needed = int(ceil(amount_left / new_per_page))

        if new_needed > 12:
            # Don't go bananas trying to get all of instagram!
            new_needed = 12

        for i in range(new_needed):  # add images x * 12
            # Keep the latest window active while loading more posts
            before_load = total_links
            body_elem.send_keys(Keys.END)
            # update server calls
            update_activity()
            sleep(1)
            body_elem.send_keys(Keys.HOME)
            sleep(1)
            link_elems = main_elem.find_elements_by_tag_name('a')
            total_links = len(link_elems)
            abort = (before_load == total_links)
            if abort:
                break

        links = [link_elem.get_attribute('href') for link_elem in link_elems
                 if link_elem.text in media]
        filtered_links = len(links)

    return links[:amount]


def get_links_for_tag(browser,
                      tag,
                      amount,
                      logger,
                      media=None,
                      skip_top_posts=True):
    """Fetches the number of links specified
    by amount and returns a list of links"""
    if media is None:
        # All known media types
        media = ['', 'Post', 'Video']
    elif media == 'Photo':
        # Include posts with multiple images in it
        media = ['', 'Post']
    else:
        # Make it an array to use it in the following part
        media = [media]

    browser.get('https://www.instagram.com/explore/tags/'
                + (tag[1:] if tag[:1] == '#' else tag))
    # update server calls
    update_activity()
    sleep(2)

    # clicking load more
    body_elem = browser.find_element_by_tag_name('body')
    sleep(2)

    abort = True

    # Get links
    if skip_top_posts:
        main_elem = browser.find_element_by_xpath('//main/article/div[2]')
    else:
        main_elem = browser.find_element_by_tag_name('main')
    total_links = 0
    links = []
    filtered_links = 0
    default_load = 21 if not skip_top_posts else 12   # !mistake change to `if not skip_top_posts`   
    #21 links with top posts (21/3=7 total rows)   #12 (12/3=4 low rows, 3 top rows) links without top posts
    while filtered_links < amount:
        if amount >= default_load:  # if amount is less to be fit in a default screen, don't scroll
            if filtered_links >= default_load:   #grab already loaded pics by default
                for i in range(5):
                    browser.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")   #scroll 12 times to get fresh a 36 pic links in it #changed range 14 cos not loading enough pics
                    update_activity()
                    sleep(1)   #if not slept, and internet speed is low, instagram will only scroll one time, instead of many times you sent scoll command...
        link_elems = main_elem.find_elements_by_tag_name('a')
        total_links =+ len(link_elems)

        try:
            if link_elems:
                new_links = [link_elem.get_attribute('href') for link_elem in link_elems
                         if link_elem and link_elem.text in media]
                for new_link in new_links:
                    links.append(new_link)
                links =  list(set(links))   #delete duplicated links
                if len(links) == filtered_links:
                    logger.info("This tag has less pictures than intended..")
                    break
                else:
                    filtered_links =+ len(links)
                if filtered_links < default_load and amount > filtered_links:
                    logger.info("This tag has so less pictures than expected...")
                    break
            else:
                logger.warning("This tag does not contain a picture")
                break

        except BaseException as e:
            logger.error("link_elems error {}".format(str(e)))
            break

    print("\n\n{} links currently : {}\n\n".format(len(links), links))

    while (filtered_links < amount) and not abort:
        amount_left = amount - filtered_links
        # Average items of the right media per page loaded
        new_per_page = ceil(12 * filtered_links / total_links)
        if new_per_page == 0:
            # Avoid division by zero
            new_per_page = 1. / 12.
        # Number of page load needed
        new_needed = int(ceil(amount_left / new_per_page))

        if new_needed > 12:
            # Don't go bananas trying to get all of instagram!
            new_needed = 12

        for i in range(new_needed):  # add images x * 12
            # Keep the latest window active while loading more posts
            before_load = total_links
            body_elem.send_keys(Keys.END)
            # update server calls
            update_activity()
            sleep(1)
            body_elem.send_keys(Keys.HOME)
            sleep(1)
            link_elems = main_elem.find_elements_by_tag_name('a')
            total_links = len(link_elems)
            abort = (before_load == total_links)
            if abort:
                break

        links = [link_elem.get_attribute('href') for link_elem in link_elems
                 if link_elem.text in media]
        filtered_links = len(links)
    
    #it keeps maximum 15 entries (minimum 9 seen) in image links of " a/'href' " location
    #with one END key press it opens average of 3 (sometimes 4 or 1 or 2 entries opens, also 5 entries did open...) new entries(in other words 3 rows) and each containing three images
    # so, to get fresh new links of pictures we must scroll 15/3 = 5 times in order to get fresh list... 
    #  and knowing that, each fresh list will contain at least 9*3 = 27 pictures and max of 15*3 = 45 pictures, since we don't care of time spent to scrolling but reliability, we should choose min of 27 pics per one scroll . so 5 scrolls gets us 27 pics 50 scrolls  = 270 ... (maybe we can take average of 36 (12*3) pics that makes average of 360 pics per 50 scrolls)
    # so we are going to get links after one fresh page scroll of 5 scrolls ..
    #scroll_bottom(amount=5)
    #get_links
    #scroll_bottom(amount5) again..
    #get_links..
    #it is getting the current page's layout and picks 15 rows of pics to put in it's " a/'href' " so it is live result, we must skip jumping to HOME after scrolling down, and must stay at the END of the page to pick the results....
    # okay the plan is taking top 12 row pic links, scrolling to get next average of 12 rows and getting pic links, then scrolling..
    #  result is 12*3 + 12*3 = 72 pics 
    #  amomunt = 200 pics
    #  we must scroll according to the amount .  . 
    #   gathered_links = 0
    #   while gathered_links < amount:
    #    for i in 12:
    #        scroll_bottom with window.scrollTo(0, document.body.scrollHeight);
    #        sleep(1)
    #    get_links
    #    gathered_links += 12*3
    #it must sleep one second before scrolling with 
    # window.scrollTo(0, document.body.scrollHeight);
    #if not slept, and internet speed is low, instagram will only scroll one time, instead of many times you sent scoll command...
    
    return links[:amount]


def get_links_for_username(browser,
                           username,
                           amount,
                           logger,
                           randomize=False,
                           media=None):

    """Fetches the number of links specified
    by amount and returns a list of links"""
    if media is None:
        # All known media types
        media = ['', 'Post', 'Video']
    elif media == 'Photo':
        # Include posts with multiple images in it
        media = ['', 'Post']
    else:
        # Make it an array to use it in the following part
        media = [media]

    logger.info('Getting {} image list...'.format(username))

    # Get  user profile page
    browser.get('https://www.instagram.com/' + username)
    # update server calls
    update_activity()

    body_elem = browser.find_element_by_tag_name('body')

    try:
        is_private = body_elem.find_element_by_xpath(
            '//h2[@class="_kcrwx"]')
    except:
        logger.info('Interaction begin...')
    else:
        if is_private:
            logger.warning('This user is private...')
            return False

    abort = True

    try:
        load_button = body_elem.find_element_by_xpath(
            '//a[contains(@class, "_1cr2e _epyes")]')
    except:
        try:
            # scroll down to load posts
            for i in range(int(ceil(amount/12))):
                browser.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                sleep(2)
        except:
            logger.warning(
                'Load button not found, working with current images!')
        else:
            abort = False
            body_elem.send_keys(Keys.END)
            sleep(2)
            # update server calls
            update_activity()
    else:
        abort = False
        body_elem.send_keys(Keys.END)
        sleep(2)
        click_element(browser, load_button) # load_button.click()
        # update server calls
        update_activity()

    body_elem.send_keys(Keys.HOME)
    sleep(2)

    # Get Links
    main_elem = browser.find_element_by_tag_name('main')
    link_elems = main_elem.find_elements_by_tag_name('a')
    total_links = len(link_elems)
    links = []
    filtered_links = 0
    try:
        if link_elems:
            links = [link_elem.get_attribute('href') for link_elem in link_elems
                     if link_elem and link_elem.text in media]
            filtered_links = len(links)

    except BaseException as e:
        logger.error("link_elems error {}}".format(str(e)))

    if randomize:
        # Expanding the pooulation for better random distribution
        amount = amount * 5

    while (filtered_links < amount) and not abort:
        amount_left = amount - filtered_links
        # Average items of the right media per page loaded
        new_per_page = ceil(12 * filtered_links / total_links)
        if new_per_page == 0:
            # Avoid division by zero
            new_per_page = 1. / 12.
        # Number of page load needed
        new_needed = int(ceil(amount_left / new_per_page))

        if new_needed > 12:
            # Don't go bananas trying to get all of instagram!
            new_needed = 12

        for i in range(new_needed):  # add images x * 12
            # Keep the latest window active while loading more posts
            before_load = total_links
            body_elem.send_keys(Keys.END)
            # update server calls
            update_activity()
            sleep(1)
            body_elem.send_keys(Keys.HOME)
            sleep(1)
            link_elems = main_elem.find_elements_by_tag_name('a')
            total_links = len(link_elems)
            abort = (before_load == total_links)
            if abort:
                break

        links = [link_elem.get_attribute('href') for link_elem in link_elems
                 if link_elem.text in media]
        filtered_links = len(links)

    if randomize:
        # Shuffle the population index
        links = random.sample(links, filtered_links)

    return links[:amount]


def check_link(browser,
               link,
               dont_like,
               ignore_if_contains,
               ignore_users,
               username,
               like_by_followers_upper_limit,
               like_by_followers_lower_limit,
               logger):

    browser.get(link)
    # update server calls
    update_activity()
    sleep(2)

    """Check if the Post is Valid/Exists"""
    try:
        post_page = browser.execute_script(
            "return window._sharedData.entry_data.PostPage")
    except WebDriverException:   #selenium Exception
        try:
            #refresh page (you would refresh twice (or more), too)
            #browser.get(link)  #method 1, when page is not loaded properly, it is not expected to reload. must be navigated to first
            browser.execute_script("location.reload()")   #mehod 2, page loaded properly, can be reloaded
            post_page = browser.execute_script(
                "return window._sharedData.entry_data.PostPage")
        except WebDriverException:
            post_page = None
    
    if post_page is None:
        logger.warning('Unavailable Page: {}'.format(link.encode('utf-8')))
        return True, None, None, 'Unavailable Page'

    """Gets the description of the link and checks for the dont_like tags"""
    graphql = 'graphql' in post_page[0]
    if graphql:
        media = post_page[0]['graphql']['shortcode_media']
        is_video = media['is_video']
        user_name = media['owner']['username']
        image_text = media['edge_media_to_caption']['edges']
        image_text = image_text[0]['node']['text'] if image_text else None
        owner_comments = browser.execute_script('''
      latest_comments = window._sharedData.entry_data.PostPage[0].graphql.shortcode_media.edge_media_to_comment.edges;
      if (latest_comments === undefined) latest_comments = Array();
      owner_comments = latest_comments
        .filter(item => item.node.owner.username == '{}')
        .map(item => item.node.text)
        .reduce((item, total) => item + '\\n' + total, '');
      return owner_comments;
    '''.format(user_name))
    else:
        media = post_page[0]['media']
        is_video = media['is_video']
        user_name = media['owner']['username']
        image_text = media['caption']
        owner_comments = browser.execute_script('''
      latest_comments = window._sharedData.entry_data.PostPage[0].media.comments.nodes;
      if (latest_comments === undefined) latest_comments = Array();
      owner_comments = latest_comments
        .filter(item => item.user.username == '{}')
        .map(item => item.text)
        .reduce((item, total) => item + '\\n' + total, '');
      return owner_comments;
    '''.format(user_name))

    if owner_comments == '':
        owner_comments = None

    """Append owner comments to description as it might contain further tags"""
    if image_text is None:
        image_text = owner_comments
    elif owner_comments:
        image_text = image_text + '\n' + owner_comments

    """If the image still has no description gets the first comment"""
    if image_text is None:
        if graphql:
            image_text = media['edge_media_to_comment']['edges']
            image_text = image_text[0]['node']['text'] if image_text else None
        else:
            image_text = media['comments']['nodes']
            image_text = image_text[0]['text'] if image_text else None
    if image_text is None:
        image_text = "No description"

    logger.info('Image from: {}'.format(user_name.encode('utf-8')))

    """Find the number of followes the user has"""
    if like_by_followers_upper_limit or like_by_followers_lower_limit:
        userlink = 'https://www.instagram.com/' + user_name
        browser.get(userlink)
        # update server calls
        update_activity()
        sleep(1)
        try:
            num_followers = browser.execute_script(
                "return window._sharedData.entry_data."
                "ProfilePage[0].user.followed_by.count")
        except WebDriverException:
            try:
                browser.execute_script("location.reload()")
                num_followers = browser.execute_script(
                    "return window._sharedData.entry_data."
                    "ProfilePage[0].user.followed_by.count")
            except WebDriverException:
                num_followers = 'undefined'
                like_by_followers_lower_limit = None
                like_by_followers_upper_limit = None
        browser.get(link)
        # update server calls
        update_activity()
        sleep(1)
        logger.info('Number of Followers: {}'.format(num_followers))

        if like_by_followers_upper_limit and \
           num_followers > like_by_followers_upper_limit:
                return True, user_name, is_video, \
                    'Number of followers exceeds limit'

        if like_by_followers_lower_limit and \
           num_followers < like_by_followers_lower_limit:
                return True, user_name, is_video, \
                    'Number of followers does not reach minimum'

    logger.info('Link: {}'.format(link.encode('utf-8')))
    logger.info('Description: {}'.format(image_text.encode('utf-8')))

    """Check if the user_name is in the ignore_users list"""
    if (user_name in ignore_users) or (user_name == username):
        return True, user_name, is_video, 'Username'

    if any((word in image_text for word in ignore_if_contains)):
        return True, user_name, is_video, 'None'

    dont_like_regex = []

    for dont_likes in dont_like:
        if dont_likes.startswith("#"):
            dont_like_regex.append(dont_likes + "([^\d\w]|$)")
        elif dont_likes.startswith("["):
            dont_like_regex.append("#" + dont_likes[1:] + "[\d\w]+([^\d\w]|$)")
        elif dont_likes.startswith("]"):
            dont_like_regex.append("#[\d\w]+" + dont_likes[1:] + "([^\d\w]|$)")
        else:
            dont_like_regex.append(
                "#[\d\w]*" + dont_likes + "[\d\w]*([^\d\w]|$)")

    for dont_likes_regex in dont_like_regex:
        quash = re.search(dont_likes_regex, image_text, re.IGNORECASE)
        if quash:
            quashed = (((quash.group(0)).split('#')[1]).split(' ')[0]).split('\n')[0]   # dismiss possible space and newlines
            iffy = ((re.split(r'\W+', dont_likes_regex))[3] if dont_likes_regex.endswith('*([^\\d\\w]|$)') else   # 'word' without format
                     (re.split(r'\W+', dont_likes_regex))[1] if dont_likes_regex.endswith('+([^\\d\\w]|$)') else   # '[word'
                      (re.split(r'\W+', dont_likes_regex))[3] if dont_likes_regex.startswith('#[\\d\\w]+') else     # ']word'
                       (re.split(r'\W+', dont_likes_regex))[1])                                                    # '#word'
            inapp_unit = ('Inappropriate! ~ contains \'{}\''.format(quashed.encode('utf-8')) if quashed == iffy else
                              'Inappropriate! ~ contains \'{}\' in \'{}\''.format(iffy.encode('utf-8'), quashed.encode('utf-8')))
            return True, user_name, is_video, inapp_unit

    return False, user_name, is_video, 'None'


def like_image(browser, username, blacklist, logger, logfolder):
    """Likes the browser opened image"""
    if quota_supervisor('likes') == 'jump':
        update_activity('jumps')
        return 'jumped'
    else:
        like_elem = browser.find_elements_by_xpath(
            "//a[@role='button']/span[text()='Like']/..")
        liked_elem = browser.find_elements_by_xpath(
            "//a[@role='button']/span[text()='Unlike']")

        if len(like_elem) == 1:
            # sleep real quick right before clicking the element
            sleep(2)
            click_element(browser, like_elem[0])

            logger.info('--> Image Liked!')
            update_activity('likes')
            if blacklist['enabled'] is True:
                action = 'liked'
                add_user_to_blacklist(
                    browser, username, blacklist['campaign'], action, logger, logfolder
                )
            sleep(2)
            return True
        elif len(liked_elem) == 1:
            logger.info('--> Already Liked!')
            return False
        else:
            logger.info('--> Invalid Like Element!')
            return False





def get_tags(browser, url):
    """Gets all the tags of the given description in the url"""
    browser.get(url)
    # update server calls
    update_activity()
    sleep(1)

    graphql = browser.execute_script(
        "return ('graphql' in window._sharedData.entry_data.PostPage[0])")
    if graphql:
        image_text = browser.execute_script(
            "return window._sharedData.entry_data.PostPage[0].graphql."
            "shortcode_media.edge_media_to_caption.edges[0].node.text")
    else:
        image_text = browser.execute_script(
            "return window._sharedData.entry_data."
            "PostPage[0].media.caption.text")

    tags = findall(r'#\w*', image_text)
    return tags
