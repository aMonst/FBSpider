# -*- encoding:utf-8-*-
# 保存lua脚本的字符串

USE_PROXY  = '''
    request:set_proxy{
        host = '%s',
        port = %d,
        username = '',
        password = '',
        type = "%s",
    }
'''

LOGIN = '''function main(splash, args)
splash:on_request(function(request)
    %s
		end)
local ok, reason = splash:go(args.url)
user_name = args.user_name
user_passwd = args.user_passwd
user_text = splash:select("#email")
pass_text = splash:select("#pass")
login_btn = splash:select("#loginbutton")
if (user_text and pass_text and login_btn) then
    user_text:send_text(user_name)
    pass_text:send_text(user_passwd)
    login_btn:mouse_click({})
end

splash:wait(math.random(5, 10))
return {
    url = splash:url(),
    cookies = splash:get_cookies(),
    headers = splash.args.headers,
 }
end'''

REQUEST_MAIN_PAGE = '''function main(splash, args)
splash:init_cookies(splash.args.cookies)
splash:on_request(function(request)
    %s
		end)
local ok, reason = splash:go(args.url)
splash:wait(math.random(5, 10))
return {
   html = splash:html(),
   headers = splash.args.headers,
   cookies = splash:get_cookies(),
 }
end'''

REQUEST_COMPLETE_PAGE = '''function main(splash, args)
splash:init_cookies(splash.args.cookies)
splash:on_request(function(request)
    %s
end)
local ok, reason = splash:go(args.url)
splash:wait(math.random(5, 10))

html  = splash:html()
old_html = ""
flush_times = %d
i = 0

while(html ~= old_html)
    do
        old_html = html
  	    splash:runjs([[window.scrollTo(0, document.body.scrollHeight)]])
		splash:wait(math.random(1,2))
  	    
		if (flush_times ~= 0 and i == flush_times) then
		    print("即将退出循环")
  	        break
  	    end
  	    
        html = splash:html()
  	    i = i + 1
    end

return {
    html = splash:html(),
    cookies = splash:get_cookies(),
}
end'''

GET_FRIEND_PAGE = '''function main(splash, args)
    splash:init_cookies(splash.args.cookies)
    splash:on_request(function(request)
        %s
    end)
    
    local ok, reason = splash:go(args.url)
    splash:wait(math.random(5, 10))
    friend_btn = splash:select("a[data-tab-key= 'friends']")
    if (friend_btn) then
        friend_btn:mouse_click({})
        splash:wait(math.random(5, 10))
    else
        return {
            hasFriend = false,
            cookie = splash:get_cookies(),
        }
    end
    
    return {
        hasFriend = true,
        html = splash:html(),
        cookie = splash:get_cookies(),
        url = splash:url(),
    }
end
'''

FLUSH_FRIEND_PAGE = '''function main(splash, args)
    splash:init_cookies(splash.args.cookies)
    splash:on_request(function(request)
        %s
    end)
    
    local ok, reason = splash:go(args.url)
    splash:wait(math.random(5, 10))
    
    flush_times = %d
    i = 0
    
    hr = splash:select("h3.uiHeaderTitle")
    while(not hr)
    do
        print("i = ", i)
        old_html = html
  	    splash:runjs([[window.scrollTo(0, document.body.scrollHeight)]])
		splash:wait(math.random(1,2))
  	    
		if (flush_times ~= 0 and i == flush_times) then
		    print("即将退出循环")
  	        break
  	    end
  	    
  	    i = i + 1
  	    hr = splash:select("h3.uiHeaderTitle")
    end

return {
    html = splash:html(),
    cookies = splash:get_cookies(),
}
end
'''