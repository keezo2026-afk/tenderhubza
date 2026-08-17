package za.co.tenderhub.data.repository
import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
class SearchHistoryStore(context:Context){private val prefs=context.getSharedPreferences("search_history",Context.MODE_PRIVATE);private val _items=MutableStateFlow(load());val items:StateFlow<List<String>> =_items
 private fun load()=prefs.getString("items","")!!.split("\n").filter{it.isNotBlank()}.take(10)
 fun add(query:String){val clean=query.trim();if(clean.isBlank())return;_items.value=(listOf(clean)+_items.value.filterNot{it.equals(clean,true)}).take(10);save()}
 fun remove(query:String){_items.value=_items.value.filterNot{it==query};save()};fun clear(){_items.value=emptyList();save()};private fun save(){prefs.edit().putString("items",_items.value.joinToString("\n")).apply()}
}
