/* tslint:disable */
/* eslint-disable */
/**
 * mmopdca API
 * Command-DSL-driven forecasting micro-service API only
 *
 * The version of the OpenAPI document: 0.4.0
 * Contact: gtocue510@gmail.com
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */
import * as runtime from '../runtime';
import { PlanCreateRequestToJSON, PlanResponseFromJSON, } from '../models/index';
/**
 *
 */
export class PlanApi extends runtime.BaseAPI {
    /**
     * 新しい Plan を登録する。  * `id` を省略すると `plan_<8桁>` を自動採番。 * 同じ `id` が既にあれば **409 Conflict**。
     * Create Plan
     */
    async createPlanPlanPostRaw(requestParameters, initOverrides) {
        if (requestParameters['planCreateRequest'] == null) {
            throw new runtime.RequiredError('planCreateRequest', 'Required parameter "planCreateRequest" was null or undefined when calling createPlanPlanPost().');
        }
        const queryParameters = {};
        const headerParameters = {};
        headerParameters['Content-Type'] = 'application/json';
        if (this.configuration && this.configuration.apiKey) {
            headerParameters["x-api-key"] = await this.configuration.apiKey("x-api-key"); // APIKeyHeader authentication
        }
        const response = await this.request({
            path: `/plan/`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: PlanCreateRequestToJSON(requestParameters['planCreateRequest']),
        }, initOverrides);
        return new runtime.JSONApiResponse(response, (jsonValue) => PlanResponseFromJSON(jsonValue));
    }
    /**
     * 新しい Plan を登録する。  * `id` を省略すると `plan_<8桁>` を自動採番。 * 同じ `id` が既にあれば **409 Conflict**。
     * Create Plan
     */
    async createPlanPlanPost(requestParameters, initOverrides) {
        const response = await this.createPlanPlanPostRaw(requestParameters, initOverrides);
        return await response.value();
    }
    /**
     * Delete Plan
     */
    async deletePlanPlanPlanIdDeleteRaw(requestParameters, initOverrides) {
        if (requestParameters['planId'] == null) {
            throw new runtime.RequiredError('planId', 'Required parameter "planId" was null or undefined when calling deletePlanPlanPlanIdDelete().');
        }
        const queryParameters = {};
        const headerParameters = {};
        if (this.configuration && this.configuration.apiKey) {
            headerParameters["x-api-key"] = await this.configuration.apiKey("x-api-key"); // APIKeyHeader authentication
        }
        const response = await this.request({
            path: `/plan/{plan_id}`.replace(`{${"plan_id"}}`, encodeURIComponent(String(requestParameters['planId']))),
            method: 'DELETE',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);
        return new runtime.VoidApiResponse(response);
    }
    /**
     * Delete Plan
     */
    async deletePlanPlanPlanIdDelete(requestParameters, initOverrides) {
        await this.deletePlanPlanPlanIdDeleteRaw(requestParameters, initOverrides);
    }
    /**
     * Get Plan by ID
     */
    async getPlanPlanPlanIdGetRaw(requestParameters, initOverrides) {
        if (requestParameters['planId'] == null) {
            throw new runtime.RequiredError('planId', 'Required parameter "planId" was null or undefined when calling getPlanPlanPlanIdGet().');
        }
        const queryParameters = {};
        const headerParameters = {};
        if (this.configuration && this.configuration.apiKey) {
            headerParameters["x-api-key"] = await this.configuration.apiKey("x-api-key"); // APIKeyHeader authentication
        }
        const response = await this.request({
            path: `/plan/{plan_id}`.replace(`{${"plan_id"}}`, encodeURIComponent(String(requestParameters['planId']))),
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);
        return new runtime.JSONApiResponse(response, (jsonValue) => PlanResponseFromJSON(jsonValue));
    }
    /**
     * Get Plan by ID
     */
    async getPlanPlanPlanIdGet(requestParameters, initOverrides) {
        const response = await this.getPlanPlanPlanIdGetRaw(requestParameters, initOverrides);
        return await response.value();
    }
    /**
     * List Plans
     */
    async listPlansPlanGetRaw(initOverrides) {
        const queryParameters = {};
        const headerParameters = {};
        if (this.configuration && this.configuration.apiKey) {
            headerParameters["x-api-key"] = await this.configuration.apiKey("x-api-key"); // APIKeyHeader authentication
        }
        const response = await this.request({
            path: `/plan/`,
            method: 'GET',
            headers: headerParameters,
            query: queryParameters,
        }, initOverrides);
        return new runtime.JSONApiResponse(response, (jsonValue) => jsonValue.map(PlanResponseFromJSON));
    }
    /**
     * List Plans
     */
    async listPlansPlanGet(initOverrides) {
        const response = await this.listPlansPlanGetRaw(initOverrides);
        return await response.value();
    }
}
