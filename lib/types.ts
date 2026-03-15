export interface Artifact {
  id: string
  name: string
  nameKr: string
  nameCn?: string
  author?: string
  nationalityCode?: string
  nationalityCode1?: string
  nationalityName1?: string
  nationalityCode2?: string
  nationalityName2?: string
  materialCode?: string
  materialName1?: string
  materialName2?: string
  purposeCode?: string
  purposeName1?: string
  purposeName2?: string
  purposeName3?: string
  sizeRangeCode?: string
  sizeRangeName?: string
  placeLandCode?: string
  placeLandCode1?: string
  placeLandName1?: string
  placeLandCode2?: string
  placeLandName2?: string
  designationCode?: string
  designationName1?: string
  designationInfo?: string
  sizeInfo?: string
  desc?: string
  glsv?: string
  relicNo?: string
  relicSubNo?: string
  museumCode?: string
  museumCode1?: string
  museumCode2?: string
  museumCode3?: string
  museumName1?: string
  museumName2?: string
  museumName3?: string
  imgUri?: string
  imgThumUriS?: string
  imgThumUriM?: string
  imgThumUriL?: string
  indexWord?: string
}

export interface ArtifactListResponse {
  numOfRows: number
  pageNo: number
  totalCount: number
  resultCode: string
  resultMsg: string
  list: Artifact[]
}

export interface CodeItem {
  level: number
  parentCode: string
  code: string
  name: string
  nameKr: string
  nameEn?: string
  nameCn?: string
}

export interface CodeListResponse {
  numOfRows: number
  pageNo: number
  totalCount: number
  resultCode: string
  resultMsg: string
  list: CodeItem[]
}

export interface ArtifactDetailResponse {
  totalCount: number
  resultCode: string
  resultMsg: string
  list: Artifact[]
  imageList?: {
    totalCount: number
    list: {
      id: string
      imgId: string
      imgOrder: number
      imgUri: string
      imgThumUriS: string
      imgThumUriM: string
      imgThumUriL: string
    }[]
  }
  relationList?: {
    totalCount: number
    list: {
      id: string
      reltId: string
      reltRelicName: string
      reltImgThumUriM?: string
    }[]
  }
}

// 시대(왕조) 코드 매핑
export const DYNASTY_LABELS: Record<string, string> = {
  PS06001001: '구석기',
  PS06001002: '신석기',
  PS06001003: '청동기',
  PS06001004: '철기',
  PS06001005: '고조선',
  PS06001006: '삼한',
  PS06001007: '낙랑',
  PS06001008: '가야',
  PS06001009: '백제',
  PS06001010: '신라',
  PS06001011: '고구려',
  PS06001012: '통일신라',
  PS06001013: '발해',
  PS06001014: '고려',
  PS06001018: '조선',
  PS06001019: '대한제국',
  PS06001020: '일제강점기',
  PS06001021: '현대',
}

// 도별 한글명 → GeoJSON name 매핑
export const PROVINCE_MAP: Record<string, string> = {
  서울특별시: '서울특별시',
  부산광역시: '부산광역시',
  대구광역시: '대구광역시',
  인천광역시: '인천광역시',
  광주광역시: '광주광역시',
  대전광역시: '대전광역시',
  울산광역시: '울산광역시',
  경기도: '경기도',
  강원도: '강원도',
  충청북도: '충청북도',
  충청남도: '충청남도',
  전라북도: '전북특별자치도',
  전라남도: '전라남도',
  경상북도: '경상북도',
  경상남도: '경상남도',
  제주도: '제주특별자치도',
  세종특별자치시: '세종특별자치시',
}

export const DESIGNATION_COLORS: Record<string, string> = {
  국보: '#e63946',
  보물: '#f4a261',
  사적: '#2a9d8f',
  천연기념물: '#57cc99',
  무형문화재: '#8338ec',
  민속문화재: '#fb8500',
}
