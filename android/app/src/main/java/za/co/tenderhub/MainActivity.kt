package za.co.tenderhub
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.flow.MutableStateFlow
import za.co.tenderhub.ui.navigation.*
import za.co.tenderhub.ui.theme.TenderHubTheme
class MainActivity:ComponentActivity(){private val deepLink=MutableStateFlow<String?>(null);override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);handle(intent);setContent{TenderHubTheme{val app=(application as TenderHubApplication);val vm:AuthViewModel=viewModel(factory=object:androidx.lifecycle.ViewModelProvider.Factory{override fun <T:androidx.lifecycle.ViewModel> create(modelClass:Class<T>):T{@Suppress("UNCHECKED_CAST")return AuthViewModel(app.authRepository) as T}});AppNavigation(vm,app.authRepository,app.tenderRepository,app.savedRepository,app.profileRepository,app.searchHistory,app.notificationRepository,app.pushRegistration,deepLink)}}}override fun onNewIntent(intent:Intent){super.onNewIntent(intent);handle(intent)}private fun handle(intent:Intent?){val uri=intent?.data?:return;deepLink.value=if(uri.host=="tender")uri.pathSegments.firstOrNull() else if(uri.host=="notifications")"notifications" else null}}
