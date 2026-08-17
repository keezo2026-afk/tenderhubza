package za.co.tenderhub.ui.navigation
import android.widget.Toast
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import za.co.tenderhub.data.repository.*
import za.co.tenderhub.ui.screens.*
private fun <T:ViewModel> factory(create:()->T)=object:ViewModelProvider.Factory{override fun <V:ViewModel> create(modelClass:Class<V>):V{@Suppress("UNCHECKED_CAST") return create() as V}}
@Composable fun AppNavigation(vm:AuthViewModel,auth:AuthRepository,tenders:TenderRepository,saved:SavedRepository,profiles:ProfileRepository,history:SearchHistoryStore){
 val nav=rememberNavController();val state by vm.state.collectAsState();val context=LocalContext.current;val navigateMain:(String)->Unit={nav.navigate(it){launchSingleTop=true}}
 val search:SearchViewModel=viewModel(factory=factory{SearchViewModel(tenders,history)});val saveController:SaveControllerViewModel=viewModel(factory=factory{SaveControllerViewModel(saved)});val savedIds by saveController.savedIds.collectAsState();val saveMessage by saveController.message.collectAsState();val savedSearches:SavedSearchesViewModel=viewModel(factory=factory{SavedSearchesViewModel(saved)})
 LaunchedEffect(saveMessage){saveMessage?.let{Toast.makeText(context,it,Toast.LENGTH_LONG).show();saveController.clearMessage()}}
 LaunchedEffect(state){when(state){is AuthState.Authenticated->{savedSearches.load();nav.navigate(Routes.Home){popUpTo(0)}};AuthState.Anonymous->{saved.clear();if(nav.currentDestination?.route !in setOf(Routes.Welcome,Routes.Login,Routes.SignUp,Routes.Forgot))nav.navigate(Routes.Welcome){popUpTo(0)}};else->Unit}}
 NavHost(nav,Routes.Splash){
  composable(Routes.Splash){SplashScreen()};composable(Routes.Welcome){WelcomeScreen({nav.navigate(Routes.Login)},{nav.navigate(Routes.SignUp)})};composable(Routes.Login){LoginScreen(state,vm::login,{nav.navigate(Routes.Forgot)},{nav.navigate(Routes.SignUp)})};composable(Routes.SignUp){SignUpScreen(state,vm::register)}
  composable(Routes.Forgot){val reset:PasswordResetViewModel=viewModel(factory=factory{PasswordResetViewModel(auth)});val resetState by reset.state.collectAsState();ForgotScreen(resetState,{reset.request(it)},{token,password->reset.confirm(token,password)}){nav.navigate(Routes.Login){popUpTo(Routes.Forgot){inclusive=true}}}}
  composable(Routes.Home){val home:HomeViewModel=viewModel(factory=factory{HomeViewModel(tenders)});val data by home.state.collectAsState();val ids=(data as? DataState.Success)?.data?.let{it.latest+it.closing_soon+it.recently_added}?.map{it.id}.orEmpty();LaunchedEffect(ids){saveController.refresh(ids)};MainShell(Routes.Home,navigateMain){padding->androidx.compose.foundation.layout.Box(Modifier.padding(padding)){HomeDataScreen(data,{home.load()},{nav.navigate(Routes.detail(it))},savedIds,{saveController.toggle(it)},{sort->search.search("",search.filters,sort);nav.navigate(Routes.Search)})}}}
  composable(Routes.Search){val data by search.state.collectAsState();val geo by search.geography.collectAsState();val historyItems by search.historyItems.collectAsState();val ids=(data as? DataState.Success)?.data?.items?.map{it.id}.orEmpty();LaunchedEffect(ids){saveController.refresh(ids)};MainShell(Routes.Search,navigateMain){padding->androidx.compose.foundation.layout.Box(Modifier.padding(padding)){SearchDataScreen(data,search.filters,geo,{q,f,s->search.search(q,f,s)},{search.search()},{search.loadMore()},{nav.navigate(Routes.detail(it))},savedIds,{saveController.toggle(it)},historyItems,search::clearHistory,search::removeHistory,{name,q,f,s->savedSearches.create(name,q,f,s)})}}}
  composable(Routes.Saved){val model:SavedTendersViewModel=viewModel(factory=factory{SavedTendersViewModel(saved)});val data by model.state.collectAsState();val ids=(data as? DataState.Success)?.data?.items?.map{it.id}.orEmpty();LaunchedEffect(ids){saveController.refresh(ids)};MainShell(Routes.Saved,navigateMain){padding->androidx.compose.foundation.layout.Box(Modifier.padding(padding)){SavedTendersScreen(data,savedIds,{model.load()},{nav.navigate(Routes.Search)},{nav.navigate(Routes.detail(it))},{saveController.toggle(it){model.load()}},{model.loadMore()})}}}
  composable(Routes.SavedSearches){val data by savedSearches.state.collectAsState();SavedSearchesScreen(data,{savedSearches.load()},{item->search.search(item.query,item.toFilters(),item.sort);nav.navigate(Routes.Search)},{item,name->savedSearches.rename(item,name)},{savedSearches.delete(it)})}
  composable(Routes.Notifications){MainFeatureScreen("Notifications",Routes.Notifications,navigateMain)}
  composable(Routes.Profile){val profile:ProfileViewModel=viewModel(factory=factory{ProfileViewModel(profiles)});val data by profile.state.collectAsState();ProfileScreen(data,{profile.load()},{profile.update(it)})}
  composable(Routes.Account){AccountMenuScreen({nav.navigate(Routes.Profile)},{nav.navigate(Routes.Saved)},{nav.navigate(Routes.SavedSearches)},{nav.navigate(Routes.Forgot)},vm::logout)}
  composable(Routes.Detail,arguments=listOf(navArgument("id"){type=NavType.StringType})){entry->val id=entry.arguments?.getString("id")!!;val detail:DetailViewModel=viewModel(key=id,factory=factory{DetailViewModel(id,tenders)});val data by detail.state.collectAsState();LaunchedEffect(id){saveController.refresh(listOf(id))};TenderDetailScreen(data,{detail.load()},id in savedIds,{saveController.toggle(id)})}
 }
}
