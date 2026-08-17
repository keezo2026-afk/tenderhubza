package za.co.tenderhub

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.flow.MutableStateFlow
import za.co.tenderhub.ui.navigation.AppNavigation
import za.co.tenderhub.ui.navigation.AuthViewModel
import za.co.tenderhub.ui.theme.TenderHubTheme

internal fun resolveTenderHubDeepLink(uri: Uri?): String? = when (uri?.host) {
    "tender" -> uri.pathSegments.firstOrNull()?.takeIf { it.isNotBlank() }
    "notifications" -> "notifications"
    else -> null
}

class MainActivity : ComponentActivity() {
    private val deepLink = MutableStateFlow<String?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        handle(intent)
        setContent {
            TenderHubTheme {
                val app = application as TenderHubApplication
                val authViewModel: AuthViewModel = viewModel(
                    factory = object : ViewModelProvider.Factory {
                        override fun <T : ViewModel> create(modelClass: Class<T>): T {
                            @Suppress("UNCHECKED_CAST")
                            return AuthViewModel(app.authRepository) as T
                        }
                    }
                )
                AppNavigation(
                    vm = authViewModel,
                    auth = app.authRepository,
                    tenders = app.tenderRepository,
                    saved = app.savedRepository,
                    profiles = app.profileRepository,
                    history = app.searchHistory,
                    notificationRepo = app.notificationRepository,
                    push = app.pushRegistration,
                    deepLink = deepLink,
                )
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handle(intent)
    }

    private fun handle(intent: Intent?) {
        deepLink.value = resolveTenderHubDeepLink(intent?.data)
    }
}
