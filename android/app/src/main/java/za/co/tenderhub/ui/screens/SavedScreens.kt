package za.co.tenderhub.ui.screens
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import za.co.tenderhub.domain.model.*
@Composable fun SavedTendersScreen(state:DataState<SearchResults>,savedIds:Set<String>,onRetry:()->Unit,onSearch:()->Unit,onTender:(String)->Unit,onSave:(String)->Unit,onLoadMore:()->Unit){when(state){DataState.Loading->Centered("Loading saved tenders…");DataState.Empty->Column(Modifier.fillMaxSize().padding(32.dp),verticalArrangement=Arrangement.Center){Text("You haven't saved any tenders yet.",style=MaterialTheme.typography.titleLarge);Button(onSearch){Text("Search tenders")}};is DataState.Error->Column(Modifier.padding(32.dp)){Text(state.message);Button(onRetry){Text("Retry")}};is DataState.Success->LazyColumn(Modifier.fillMaxSize().padding(16.dp)){item{Text("Saved tenders",style=MaterialTheme.typography.headlineMedium)};items(state.data.items,key={it.id}){tender->Column{TenderCardView(tender,tender.id in savedIds,{onSave(tender.id)}){onTender(tender.id)};state.data.savedAt[tender.id]?.let{Text("Saved: ${it.take(10)}",style=MaterialTheme.typography.labelMedium)}}};if(state.data.page<state.data.totalPages)item{Button(onLoadMore,Modifier.fillMaxWidth()){Text("Load more")}}}}}
@Composable fun SavedSearchesScreen(state:DataState<List<SavedSearch>>,onRetry:()->Unit,onRun:(SavedSearch)->Unit,onRename:(SavedSearch,String)->Unit,onDelete:(SavedSearch)->Unit,onToggleAlerts:(SavedSearch)->Unit){
 var rename by remember{mutableStateOf<SavedSearch?>(null)}
 when(state){
  DataState.Loading->Centered("Loading saved searches…")
  DataState.Empty->Centered("No saved searches yet.")
  is DataState.Error->Column(Modifier.padding(32.dp)){Text(state.message);Button(onRetry){Text("Retry")}}
  is DataState.Success->LazyColumn(Modifier.fillMaxSize().padding(16.dp)){
   item{Text("Saved searches",style=MaterialTheme.typography.headlineMedium)}
   items(state.data,key={it.id}){savedSearch->Card(Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(16.dp)){Text(savedSearch.name,style=MaterialTheme.typography.titleMedium);if(savedSearch.query.isNotBlank())Text(savedSearch.query);TextButton({onToggleAlerts(savedSearch)}){Text(if(savedSearch.alerts_enabled)"🔔 Alerts ON" else "Alerts OFF")};Row{TextButton({onRun(savedSearch)}){Text("Run Search")};TextButton({rename=savedSearch}){Text("Rename")};TextButton({onDelete(savedSearch)}){Text("Delete")}}}}}
  }
 }
 rename?.let{savedSearch->var name by remember(savedSearch){mutableStateOf(savedSearch.name)};AlertDialog(onDismissRequest={rename=null},title={Text("Rename search")},text={OutlinedTextField(name,{name=it})},confirmButton={TextButton({onRename(savedSearch,name);rename=null}){Text("Save")}},dismissButton={TextButton({rename=null}){Text("Cancel")}})}
}
@Composable fun ProfileScreen(state:DataState<Profile>,onRetry:()->Unit,onUpdate:(ProfileUpdate)->Unit){when(state){DataState.Loading->Centered("Loading profile…");DataState.Empty->Centered("Profile unavailable");is DataState.Error->Column(Modifier.padding(32.dp)){Text(state.message);Button(onRetry){Text("Retry")}};is DataState.Success->{val p=state.data;var first by remember(p){mutableStateOf(p.first_name)};var last by remember(p){mutableStateOf(p.last_name)};var phone by remember(p){mutableStateOf(p.phone?:"")};var province by remember(p){mutableStateOf(p.province?:"")};var city by remember(p){mutableStateOf(p.city?:"")};Column(Modifier.fillMaxSize().padding(24.dp)){Text("Profile",style=MaterialTheme.typography.headlineMedium);FieldInput("First name",first){first=it};FieldInput("Last name",last){last=it};FieldInput("Phone",phone){phone=it};FieldInput("Province",province){province=it};FieldInput("City",city){city=it};Button({onUpdate(ProfileUpdate(first,last,phone.ifBlank{null},province.ifBlank{null},city.ifBlank{null}))},enabled=first.isNotBlank()&&last.isNotBlank()){Text("Save profile")}}}}}
@Composable fun AccountMenuScreen(onProfile:()->Unit,onSaved:()->Unit,onSearches:()->Unit,onSecurity:()->Unit,onNotificationSettings:()->Unit,onLogout:()->Unit){Column(Modifier.fillMaxSize().padding(24.dp)){Text("Account",style=MaterialTheme.typography.headlineLarge);MenuButton("Profile",onProfile);MenuButton("Saved tenders",onSaved);MenuButton("Saved searches",onSearches);MenuButton("Business profile — NOT IMPLEMENTED",{});MenuButton("Notification settings",onNotificationSettings);MenuButton("Subscription — NOT IMPLEMENTED",{});MenuButton("Password & security",onSecurity);Button(onLogout){Text("Log out")}}}
@Composable private fun MenuButton(label:String,onClick:()->Unit){TextButton(onClick,Modifier.fillMaxWidth()){Text(label)}}
@Composable private fun FieldInput(label:String,value:String,onValue:(String)->Unit){OutlinedTextField(value,onValue,label={Text(label)},modifier=Modifier.fillMaxWidth())}
@Composable private fun Centered(message:String){Column(Modifier.fillMaxSize().padding(32.dp),verticalArrangement=Arrangement.Center){Text(message)}}
