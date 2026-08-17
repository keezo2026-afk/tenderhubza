package za.co.tenderhub.data.repository
import za.co.tenderhub.data.remote.TenderHubApi
import za.co.tenderhub.domain.model.*
interface TenderRepository{suspend fun home():ApiResult<HomeResponse>;suspend fun search(q:String,page:Int,filters:TenderFilters=TenderFilters(),sort:String="relevance"):ApiResult<Page<Tender>>;suspend fun detail(id:String):ApiResult<TenderDetail>;suspend fun provinces():ApiResult<List<Province>>;suspend fun districts():ApiResult<List<District>>;suspend fun municipalities():ApiResult<List<Municipality>>}
class NetworkTenderRepository(private val api:TenderHubApi):TenderRepository{
 override suspend fun home()=apiCall{api.home()}
 override suspend fun search(q:String,page:Int,filters:TenderFilters,sort:String)=apiCall{api.tenders(q.ifBlank{null},page,20,filters.provinceId,filters.districtId,filters.municipalityId,filters.category.ifBlank{null},filters.tenderType.ifBlank{null},filters.status.ifBlank{null},filters.closingFrom.ifBlank{null},filters.closingTo.ifBlank{null},filters.issueFrom.ifBlank{null},filters.issueTo.ifBlank{null},filters.minValue.ifBlank{null},filters.maxValue.ifBlank{null},sort)}
 override suspend fun detail(id:String)=apiCall{api.tender(id)};override suspend fun provinces()=apiCall{api.provinces()};override suspend fun districts()=apiCall{api.districts()};override suspend fun municipalities()=apiCall{api.municipalities()}
}
