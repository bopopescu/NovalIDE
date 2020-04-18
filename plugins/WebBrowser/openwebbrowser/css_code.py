css_code = '''
    <style type="text/css">
        body {
            background-color: #222;
            color: #bbb;
            line-height: 1.5;
        }
        a{ color: cornflowerblue; }
        .monaco-workbench .welcomePageContainer {
            align-items: center;
            display: flex;
            justify-content: center;
            min-width: 100%;
            min-height: 100%;
        }

        .monaco-workbench .welcomePage {
            width: 90%;
            max-width: 1200px;
            font-size: 10px;
        }

        .monaco-workbench .welcomePage .row {
            display: flex;
            flex-flow: row;
        }

        .monaco-workbench .welcomePage .row .section {
            overflow: hidden;
        }

        .monaco-workbench .welcomePage .row .splash {
            overflow: hidden;
        }

        .monaco-workbench .welcomePage .row .commands {
            overflow: hidden;
        }

        .monaco-workbench .welcomePage .row .commands .list {
            overflow: hidden;
        }

        .monaco-workbench .welcomePage p {
            font-size: 1.3em;
        }

        .monaco-workbench .welcomePage .keyboard {
            font-family: "Lucida Grande", sans-serif;/* Keyboard shortcuts */
        }

        .monaco-workbench .welcomePage a {
            text-decoration: none;
        }

        .monaco-workbench .welcomePage a:focus {
            outline: 1px solid -webkit-focus-ring-color;
            outline-offset: -1px;
        }

        .monaco-workbench .welcomePage h1 {
            padding: 0;
            margin: 0;
            border: none;
            font-weight: normal;
            font-size: 3.6em;
            white-space: nowrap;
            
        }
        h1, h2{ color: #ccc; }
        h3{ color: #fff; }

        .monaco-workbench .welcomePage .title {
            margin-top: 1em;
            margin-bottom: 1em;
            flex: 1 100%;
        }

        .monaco-workbench .welcomePage .subtitle {
            margin-top: .8em;
            font-size: 2.6em;
            display: block;
            color: #aaa;
        }

        .hc-black .monaco-workbench .welcomePage .subtitle {
            font-weight: 200;
        }

        .monaco-workbench .welcomePage .splash,
        .monaco-workbench .welcomePage .commands {
            flex: 1 1 0;
        }

        .monaco-workbench .welcomePage h2 {
            font-weight: 200;
            margin-top: 17px;
            margin-bottom: 5px;
            font-size: 1.9em;
            line-height: initial;
        }

        .monaco-workbench .welcomePage .splash .section {
            margin-bottom: 5em;
        }

        .monaco-workbench .welcomePage .splash ul {
            margin: 0;
            font-size: 1.3em;
            list-style: none;
            padding: 0;
        }

        .monaco-workbench .welcomePage .splash li {
            min-width: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .monaco-workbench .welcomePage.emptyRecent .splash .recent .list {
            display: none;
        }
        .monaco-workbench .welcomePage .splash .recent .none {
            display: none;
        }
        .monaco-workbench .welcomePage.emptyRecent .splash .recent .none {
            display: initial;
        }

        .monaco-workbench .welcomePage .splash .recent li.moreRecent {
            margin-top: 5px;
        }

        .monaco-workbench .welcomePage .splash .recent .path {
            padding-left: 0em;
        }

        .monaco-workbench .welcomePage .splash .title,
        .monaco-workbench .welcomePage .splash .showOnStartup {
            min-width: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .monaco-workbench .welcomePage .splash .showOnStartup > .checkbox {
            vertical-align: bottom;
        }

        .monaco-workbench .welcomePage .commands .list {
            list-style: none;
            padding: 0;
        }
        .monaco-workbench .welcomePage .commands .item {
            margin: 7px 0px;

        }
        .monaco-workbench .welcomePage .commands .item button {
            margin: 1px;
            padding: 12px 10px;
            width: calc(100% - 2px);
            height: 5em;
            font-size: 1.3em;
            text-align: left;
            cursor: pointer;
            white-space: nowrap;
            font-family: inherit;
            color: #ccc;
            background-color: #111;
            opacity:0.6;
            filter:alpha(opacity=60);

        }
        .monaco-workbench .welcomePage .commands .item button:hover{
            background-color: #333;
        }

        .monaco-workbench .welcomePage .commands .item button > span {
            display: inline-block;
            width:100%;
            min-width: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: #aaa;
        }

        .monaco-workbench .welcomePage .commands .item button h3 {
            font-weight: normal;
            font-size: 1em;
            margin: 0;
            margin-bottom: .25em;
            min-width: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .monaco-workbench .welcomePage .commands .item button {
            border: none;
        }

        .hc-black .monaco-workbench .welcomePage .commands .item button > h3 {
            font-weight: bold;
        }

        .monaco-workbench .welcomePage .commands .item button:focus {
            outline-style: solid;
            outline-width: 1px;
        }

        .hc-black .monaco-workbench .welcomePage .commands .item button {
            border-width: 1px;
            border-style: solid;
        }

        .hc-black .monaco-workbench .welcomePage .commands .item button:hover {
            outline-width: 1px;
            outline-style: dashed;
            outline-offset: -5px;
        }

        .monaco-workbench .welcomePage .commands .item button .enabledExtension {
            display: none;
        }
        .monaco-workbench .welcomePage .commands .item button .installExtension.installed {
            display: none;
        }
        .monaco-workbench .welcomePage .commands .item button .enabledExtension.installed {
            display: inline;
        }

        .monaco-workbench .welcomePageContainer.max-height-685px .title {
            display: none;
        }

        .file-icons-enabled .show-file-icons .vs_code_welcome_page-name-file-icon.file-icon::before {
            content: ' ';
            background-image: url('../../code-icon.svg');
        }

        .monaco-workbench .welcomePage .mac-only,
        .monaco-workbench .welcomePage .windows-only,
        .monaco-workbench .welcomePage .linux-only {
            display: none;
        }
        .monaco-workbench.mac .welcomePage .mac-only {
            display: initial;
        }
        .monaco-workbench.windows .welcomePage .windows-only {
            display: initial;
        }
        .monaco-workbench.linux .welcomePage .linux-only {
            display: initial;
        }
        .monaco-workbench.mac .welcomePage li.mac-only {
            display: list-item;
        }
        .monaco-workbench.windows .welcomePage li.windows-only {
            display: list-item;
        }
        .monaco-workbench.linux .welcomePage li.linux-only {
            display: list-item;
        }

    </style>
'''