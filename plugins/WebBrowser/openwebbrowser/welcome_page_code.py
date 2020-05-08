from noval import _,GetApp
content_code = '''
<div class="monaco-workbench windows">
    <div class="welcomePageContainer">
        <div class="welcomePage" id="welcome">
            <div class="row">
                <div class="splash">
                    <div class="section start">
                        <h2 class="caption">{0}</h2>
                        <ul>
                            <li><a href="#" onclick="NewProject()">{1}</a></li>
                            <li class="windows-only linux-only"><a href="#" onclick="OpenProject()">{2}</a></li>
                        </ul>
                    </div>
                    <div class="section recent">
                        <h2 class="caption">{3}</h2>
                        <ul class="list" id="recent">
                        </ul>
                        <p class="none detail">{4}</p>
                    </div>
                    <div class="section help">
                        <h2 class="caption">{5}</h2>
                        <ul>
                            <li><a href="#" onclick="Command.action('command:workbench.action.help.keybindingsReference')">{12}</a></li>
                            <li><a href="command:workbench.action.openIntroductoryVideosUrl">Introductory videos</a></li>
                            <li><a href="command:workbench.action.openTipsAndTricksUrl">Tips and Tricks</a></li>
                            <li><a href="javascript:void(0)" onclick="Command.action('command:workbench.action.help.openDocumentationUrl')">{11}</a></li>
                            <li><a href="javascript:void(0)" onclick="Command.action('command:workbench.action.help.openCodeRepositoryURL')">{8}</a></li>
                            <li><a href="javascript:void(0)" onclick="Command.action('command:workbench.action.help.register_or_login')">{9}</a></li>
                            <li><a href="#" onclick="Command.action('command:workbench.action.help.ManagePlugins')">{10}</a></li>
                        </ul>
                    </div>
                </div>
                <div class="commands">
                    <div class="section news">
                        <h2 class="caption">{6}</h2>
                        <div class="list" id="news">
                        <p class="none detail">{13}</p>
                        </div>
                    </div>
                    <div class="section learn">
                        <h2 class="caption">{7}</h2>
                        <div class="list" id="learn">
                        <p class="none detail">{13}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
'''.format(_('Start'),_('New project'),_('Open project...'),_('Recent'),_('No recent projects'),_('Help'),_('News'),_('Learn'),_('Code repository'),_('Register&Login'),_('Manage Plugins'),_("Product documentation"),\
           _("Printable keyboard cheatsheet"),_("loading..."))