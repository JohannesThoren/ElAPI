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

setInterval(() => {

    let root = Div(H("Ellevio"))

    fetch("http://localhost:5500/Ellevio/outdata.json").then(resp => resp.json()).then(data => {

        data["outages"].forEach(outage => {

            let m = H(outage["municipality"], 2)
            let st = P(outage["start_time"])
            let et = P(outage["end_time"])
            let inf = P(outage["info_text"])
            let lu = P(outage["last_update"])
            let img = Img("./Ellevio/" + outage["municipality"] + ".png", outage["municipality"] + " image").Class("municipality-img")

            let wrapper = Div(m, st, et, inf, lu, img)
            root.Child(wrapper)

        })


        document.querySelector("body").removeChild(document.querySelector("body").lastChild)
        document.querySelector("body").appendChild(root)
    })




}, 500)