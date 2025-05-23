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

import { mapValues } from '../runtime';
import type { DoStatus } from './DoStatus';
import {
    DoStatusFromJSON,
    DoStatusFromJSONTyped,
    DoStatusToJSON,
    DoStatusToJSONTyped,
} from './DoStatus';

/**
 * Do ジョブの状態および結果レスポンス。
 * 
 * `status` 遷移: **PENDING → RUNNING → (DONE | FAILED)**
 * @export
 * @interface DoResponse
 */
export interface DoResponse {
    /**
     * Do 実行 ID (`do-xxxx` 形式)
     * @type {string}
     * @memberof DoResponse
     */
    doId: string;
    /**
     * 紐づく Plan ID
     * @type {string}
     * @memberof DoResponse
     */
    planId: string;
    /**
     * DoCreateRequest.run_no のエコーバック（互換: 'seq'）
     * @type {number}
     * @memberof DoResponse
     */
    seq: number;
    /**
     * 
     * @type {string}
     * @memberof DoResponse
     */
    runTag?: string | null;
    /**
     * ジョブ状態
     * @type {DoStatus}
     * @memberof DoResponse
     */
    status: DoStatus;
    /**
     * 
     * @type {object}
     * @memberof DoResponse
     */
    result?: object | null;
    /**
     * 
     * @type {string}
     * @memberof DoResponse
     */
    artifactUri?: string | null;
    /**
     * 
     * @type {string}
     * @memberof DoResponse
     */
    dashboardUrl?: string | null;
}



/**
 * Check if a given object implements the DoResponse interface.
 */
export function instanceOfDoResponse(value: object): value is DoResponse {
    if (!('doId' in value) || value['doId'] === undefined) return false;
    if (!('planId' in value) || value['planId'] === undefined) return false;
    if (!('seq' in value) || value['seq'] === undefined) return false;
    if (!('status' in value) || value['status'] === undefined) return false;
    return true;
}

export function DoResponseFromJSON(json: any): DoResponse {
    return DoResponseFromJSONTyped(json, false);
}

export function DoResponseFromJSONTyped(json: any, ignoreDiscriminator: boolean): DoResponse {
    if (json == null) {
        return json;
    }
    return {
        
        'doId': json['do_id'],
        'planId': json['plan_id'],
        'seq': json['seq'],
        'runTag': json['run_tag'] == null ? undefined : json['run_tag'],
        'status': DoStatusFromJSON(json['status']),
        'result': json['result'] == null ? undefined : json['result'],
        'artifactUri': json['artifact_uri'] == null ? undefined : json['artifact_uri'],
        'dashboardUrl': json['dashboard_url'] == null ? undefined : json['dashboard_url'],
    };
}

export function DoResponseToJSON(json: any): DoResponse {
    return DoResponseToJSONTyped(json, false);
}

export function DoResponseToJSONTyped(value?: DoResponse | null, ignoreDiscriminator: boolean = false): any {
    if (value == null) {
        return value;
    }

    return {
        
        'do_id': value['doId'],
        'plan_id': value['planId'],
        'seq': value['seq'],
        'run_tag': value['runTag'],
        'status': DoStatusToJSON(value['status']),
        'result': value['result'],
        'artifact_uri': value['artifactUri'],
        'dashboard_url': value['dashboardUrl'],
    };
}

