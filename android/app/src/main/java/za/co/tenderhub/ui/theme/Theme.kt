package za.co.tenderhub.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val TenderHubLightColors = lightColorScheme(
    primary = Color(0xFF006B5B),
    onPrimary = Color.White,
    secondary = Color(0xFF4B635D),
    background = Color(0xFFFAFDFB),
    surface = Color.White,
    error = Color(0xFFBA1A1A),
)

@Composable
fun TenderHubTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = TenderHubLightColors,
        typography = Typography(),
        content = content,
    )
}
