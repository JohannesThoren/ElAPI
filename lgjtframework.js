// Copyright 2024 johannes
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * 
 * @param {*} name 
 * @param  {...any} children 
 * @returns 
 */
function Tag(name, ...children) {
    let tag = document.createElement(name);
  
    tag.OnAppend = (call = function () { return }) => { call(); return tag; }
  
  
    tag.Arg = (name, value) => {
      tag.setAttribute(name, value);
      return tag
    }
  
    tag.Id = (name) => {
      tag.Arg('id', name);
      return tag;
    }
  
    tag.Class = (name) => {
      tag.Arg('class', name);
      return tag;
    }
  
    tag.Child = (child) => {
      if (child.OnAppend) {
        child.OnAppend()
      }
      tag.appendChild(child);
  
      return tag;
    }
  
    children.forEach(child => tag.Child(child));
  
    return tag
  }
  
  function Text(text) {
    let textNode = document.createTextNode(text);
    return textNode;
  }
  
  function Div(...children) {
    return Tag('div', ...children);
  }
  
  function H(text, level = 1) {
    return Tag('h' + level, Text(text));
  }
  
  function P(text) {
    return Tag('p', Text(text));
  }
  
  function A(text, link) {
    return Tag('a', Text(text)).Arg("href", link)
  }
  
  function Li(...children) {
    return Tag('li', ...children);
  }
  
  function Ol(...children) {
    return Tag('ol', ...children);
  }
  
  function Ul(...children) {
    return Tag('ul', ...children);
  }
  
  function Img(src, alt) {
    return Tag('img').Arg("src", src).Arg("alt", alt)
  }
  
  function Button(text, click) {
    let button = Tag('button').Child(Text(text));
    button.addEventListener('click', click);
    return button;
  }
  
  /**
   * 
   * @param {*} name 
   * @param {*} body 
   * @returns 
   */
  function Tab(name, body) {
    return { name: name, body: body }
  }
  
  /**
   * 
   * @param  {...any} tabs 
   * @returns 
   */
  function TabRoot(...tabs) {
    let tabNav = Div().Id("tab-nav");
    let tabBody = Div().Id("tab-body");
    let tabRoot = Div().Id("tab-root");;
  
  
    tabs.forEach(tab => {
      let btn = Button(tab.name, () => {
        tabBody.replaceChildren(tab.body);
        tabRoot.Active.button.Arg("data-active", false)
        tabRoot.Active = { button: btn, body: tab.body, name: tab.name }
        tabRoot.Active.button.Arg("data-active", true)
  
      }).Class("tab-nav-item").Arg("data-tab", tab.name).Arg("data-active", false);
  
      tabNav.Child(btn)
  
    })
  
    tabRoot.Active = { button: tabNav.children[0], body: tabs[0].body, name: tabs[0].name };
    tabBody.replaceChildren(tabRoot.Active.body);
    tabRoot.Active.button.Arg("data-active", true)
  
  
    return tabRoot.Child(tabNav).Child(tabBody);
  }
  
  /**
   * 
   * @param {*} path 
   * @param {*} body 
   * @returns 
   */
  
  function RouterLink(text, route, router) {
    let link = A(text, "#" + route)
    return link
  }
  
  function Route(path, body, ...subRoutes) {
    return {
      path: path,
      body: body,
      GetSubRoutes: () => {
        let list = []
  
        if (subRoutes.length == 0)
          return list
  
        subRoutes.forEach((r) => {
          r.GetSubRoutes().forEach(sr => {
            sr.path = r.path + sr.path
            list.push(sr)
          })
  
          list.push(r)
        })
  
        return list
      },
    }
  }
  
  function RouterHandleHashChange(routingTable) {
  
  
    let currentRoute = window.location.hash.split("#")[1] == undefined ? "/" : window.location.hash.split("#")[1]
  
  
    if (routingTable[currentRoute] == undefined) {
      window.location.href = "#/404"
      RouterHandleHashChange(routingTable)
      return
    }
  
    if (currentRoute.startsWith("/"))
      document.querySelector("#router-body").replaceChildren(routingTable[currentRoute])
  }
  
  function Router() {
    let Router = {}
  
    Router.routingTable = {}
  
    Router.AddRoutes = (...routes) => {
      routes.forEach(r => {
        router.routingTable[r.path] = r.body
  
  
        r.GetSubRoutes().forEach(sr => {
          Router.routingTable[sr.path] = sr.body
  
        })
      })
    }
  
  
    window.addEventListener("hashchange", (evt) => RouterHandleHashChange(Router.routingTable))
  
    return Router
  }
  
  function RotuerBody() {
    return Div().Id("router-body")
  }
  
  function RouterOnLoad(router) {
    // error routes
    router.AddRoutes(
      Route("/404",
        Div(
          H("ERROR: 404"),
          P("The page you are trying to reach does not exist. If you think that this is incorrect, Please contact the page adminstrator.")
        )
      )
    )
  
    document.addEventListener('load', () => {
      document.querySelector("body").appendChild(RotuerBody());
      RouterHandleHashChange(router.routingTable)
      console.log(router)
    })
  }
  
  function OnLoad(...child) {
    window.addEventListener('load', () => {
      child.forEach(c => {
        document.querySelector("body").appendChild(c);
      })
    })
  }
  