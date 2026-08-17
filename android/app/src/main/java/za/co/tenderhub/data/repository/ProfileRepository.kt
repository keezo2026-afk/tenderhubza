package za.co.tenderhub.data.repository
import za.co.tenderhub.data.remote.TenderHubApi
import za.co.tenderhub.domain.model.*
class ProfileRepository(private val api:TenderHubApi){suspend fun get()=apiCall{api.profile()};suspend fun update(value:ProfileUpdate)=apiCall{api.updateProfile(value)}}
