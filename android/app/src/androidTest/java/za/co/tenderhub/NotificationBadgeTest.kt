package za.co.tenderhub
import androidx.compose.material3.Text
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.*
import za.co.tenderhub.ui.screens.MainShell
class NotificationBadgeTest{@get:Rule val compose=createComposeRule();@Test fun backendUnreadCountAppears(){compose.setContent{MainShell("home",{},3){Text("Content")}};compose.onNodeWithText("Alerts 3").assertIsDisplayed()}}
